package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.military.CommanderAssignmentPostcondition;
import org.xar.ck3.control.application.planning.military.CommanderBindings;
import org.xar.ck3.control.application.planning.military.CommanderObservationCollector;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerHolyOrderContextRead;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.Kind;

/** The one concrete Army17 composition. Real quotes, ten material observers and the two original delegates. */
public final class RootArmyOrdinaryRuntimeInputs {
    private RootArmyOrdinaryRuntimeInputs() { }
    public record Sources(ArmyOrdinaryActionService.Sources actions, ExactRef factory, ExactRef ordinaryObserver,
            ExactRef moveObserver, ExactRef warExitObserver, ExactRef warWindowObserver, ExactRef holyOrderDecoder, HolyHirePoststate.Sources holyPoststateSources,
            PlayerHolyOrderContextRead.Sources holyOrders,RegularMaaPrivatePermission.Sources regularMaa) {
        public Sources {
            Objects.requireNonNull(actions);Objects.requireNonNull(holyOrders);Objects.requireNonNull(regularMaa);Objects.requireNonNull(holyPoststateSources);
            for(ExactRef source:List.of(factory,ordinaryObserver,moveObserver,warExitObserver,warWindowObserver,holyOrderDecoder))
                StrictJson.require(source!=null&&source.bytes()>0,"actual complete Army factory/observer source required");
        }
    }
    public record Configuration(Duration commandTimeout,ArmyOrdinaryActionService.ActionIds actionIds) {
        public Configuration {
            Objects.requireNonNull(actionIds);
            StrictJson.require(commandTimeout!=null&&!commandTimeout.isZero()&&!commandTimeout.isNegative()
                    &&commandTimeout.compareTo(Duration.ofMinutes(1))<=0,"bounded original Army command timeout required");
        }
    }
    public static final class Prepared {
        private final Sources sources;private final Configuration configuration;
        public Prepared(Sources sources,Configuration configuration) {
            this.sources=Objects.requireNonNull(sources);this.configuration=Objects.requireNonNull(configuration);
        }
        public List<org.xar.ck3.control.nativebridge.NativePrivateActionPermission> privatePermissions(
                org.xar.ck3.control.nativebridge.NativePrivateActionPermission.QualificationVerifier actual) {
            return List.of(RegularMaaPrivatePermission.permission(sources.regularMaa(),actual));
        }
        public ArmyOrdinaryRuntimeBindings.Installed install(RootRuntimeContext context,RootRuntimeDomainAssembly.Shared shared,
                RootFamilyRuntimeFactory.Installed actualFamily) throws IOException {
            Objects.requireNonNull(context);Objects.requireNonNull(shared);Objects.requireNonNull(actualFamily);
            for(Class<?> implementation:List.of(RootArmyOrdinaryRuntimeInputs.class,NativeArmyOrdinaryEffects.class,
                    NativeArmyMoveEffects.class,NativeWarExitEffects.class,RootWarExitTruceReads.class,ArmyWarExitTruceReads.class,NativeRegularMaaSubmission.class,RegularMaaPrivatePermission.class,ArmyOrdinaryOccupationProjection.class,
                    ArmyOrdinaryPairedQuotes.class,PlayerHolyOrderContextRead.class,HolyHirePoststate.class,RootHolyHirePoststate.class))
                context.game().launchPlan().sources().requireLoadedClass(implementation);
            var army=shared.army().products();var military=shared.military();
            var holy=new PlayerHolyOrderContextRead(context.reads(),sources.holyOrders(),(original,request)->{
                try {
                    context.requireCurrent(request.deadline());context.writer().requireSession(context.borrowedSession());
                    var factual=PlayerHolyOrderContextRead.factualFrame(request);
                    StrictJson.require(original.equals(sources.holyOrders())&&factual.game().equals(context.game().generation())
                            &&factual.machineId().equals(context.game().machineId())&&request.source().equals(context.source())
                            &&request.sessionId().equals(context.game().sessionId()),"holy-order query crossed the actual Root Game/source/session");
                    context.game().launchPlan().sources().requireLoadedClass(PlayerHolyOrderContextRead.class);
                } catch(IOException unavailable) {throw new UncheckedIOException("actual holy-order Root source admission unavailable",unavailable);}
            });
            var producers=new ArmyOrdinaryPairedQuotes.Producers(army.frames(),military.warReads(),army.closedContracts(),
                    army.windowContracts(),actualFamily.obligationsContract(),holy);
            var snapshots=new NativeEffectSnapshots(()->context.adopted().observations(),context.archive(),context.frameLoader());
            var occupations=new ArmyOrdinaryOccupationProjection();
            NativeArmyOrdinaryEffects.IndependentReadPort independent=(query,command,attempt,after)->postRead(context,producers,query,command,after);
            var ordinary=new NativeArmyOrdinaryEffects(snapshots,independent,context.frameLoader(),Optional.of(occupations));
            // This is the same installed retreat proof and the same Root reconciliation consumer, never a null substitute.
            var retreatProof=army.retreatComposite().preflightVerifier();
            var move=new NativeArmyMoveEffects(snapshots,retreatProof,army.reconciliationPost());
            var truces=new RootWarExitTruceReads(context,army.warExitTruceContracts());
            var exits=new NativeWarExitEffects(snapshots,truces);
            List<ArmyOrdinaryActionService.Effect> effects=effects(sources,ordinary,move,exits,context.frameLoader(),retreatProof,army.reconciliationPost(),truces);
            var gates=new FinalGates(context,army.closedContracts(),configuration.commandTimeout());
            var inputs=new ArmyOrdinaryRuntimeBindings.Inputs(producers,sources.actions(),sources.warWindowObserver(),sources.holyOrderDecoder(),sources.holyPoststateSources(),configuration.actionIds(),
                    occupations::holdings,gates,effects,
                    (same,input,source,id)->commander(context,military.commander(),same,input,source,id),
                    (same,input,source,id)->mercenary(context,same,input,source,id),configuration.commandTimeout());
            return ArmyOrdinaryRuntimeBindings.install(context,inputs);
        }
    }
    static List<ArmyOrdinaryActionService.Effect> effects(Sources sources,NativeArmyOrdinaryEffects ordinary,
            NativeArmyMoveEffects move,NativeWarExitEffects exits,NativeEffectEvidence.FrameLoader frames,
            ArmyRetreatPreflightVerifier retreatProof,ArmyRetreatPostReadCollector retreatPost,NativeWarExitEffects.TruceReadPort truces) {
        Objects.requireNonNull(sources);Objects.requireNonNull(ordinary);Objects.requireNonNull(move);Objects.requireNonNull(exits);
        Objects.requireNonNull(frames);Objects.requireNonNull(retreatProof);Objects.requireNonNull(retreatPost);Objects.requireNonNull(truces);
        var result=new ArrayList<ArmyOrdinaryActionService.Effect>();
        for(Kind kind:EnumSet.of(Kind.RAISE_TROOPS_DEFAULT,Kind.DISBAND_ARMY,Kind.START_ASSAULT,Kind.STOP_ASSAULT,
                Kind.SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1,Kind.SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1))
            result.add(new ArmyOrdinaryActionService.Effect(kind,sources.ordinaryObserver(),ordinary,NativeArmyOrdinaryEffects::expected,
                    operation->ordinary.archivedVerifier(operation,sources.ordinaryObserver(),frames)));
        result.add(new ArmyOrdinaryActionService.Effect(Kind.MOVE_ARMY,sources.moveObserver(),move,
                (before,source,operation,arguments)->NativeArmyMoveEffects.expected(before,source,operation),
                operation->NativeArmyMoveEffects.archivedVerifier(operation,sources.moveObserver(),frames,retreatProof,retreatPost)));
        for(Kind kind:EnumSet.of(Kind.ENFORCE_DEMANDS,Kind.SURRENDER_WAR,Kind.OFFER_WHITE_PEACE))
            result.add(new ArmyOrdinaryActionService.Effect(kind,sources.warExitObserver(),exits,RootArmyOrdinaryRuntimeInputs::warExitExpected,
                    operation->NativeWarExitEffects.archivedVerifier(operation,sources.warExitObserver(),frames,truces)));
        ArmyOrdinaryRuntimeBindings.requireRemainingEffects(result);return List.copyOf(result);
    }
    static ExpectedPostcondition warExitExpected(ObservationIdentity before,G2Source source,OperationKey operation,RawJson arguments) {
        var selected=ArmyOrdinaryActionArguments.decode(arguments);
        StrictJson.require(EnumSet.of(Kind.ENFORCE_DEMANDS,Kind.SURRENDER_WAR,Kind.OFFER_WHITE_PEACE).contains(selected.kind()),
                "war exit expected producer received a different Army action");
        long war=NativeWarExitEffects.warId(operation);
        var call=ArmyCallCodec.decode(PublicMethod.valueOf(selected.kind().name()),selected.publicArguments());
        StrictJson.require(call instanceof ArmyCalls.War selectedWar&&selectedWar.warId().equals(BigInteger.valueOf(war)),
                "war exit expected producer crossed the selected original full WarID");
        String prefix=switch(selected.kind()) {case ENFORCE_DEMANDS->"enforce-demands-";case SURRENDER_WAR->"surrender-war-";case OFFER_WHITE_PEACE->"offer-white-peace-";default->throw new IllegalArgumentException("not a terminal war action");};
        StrictJson.require(operation.value().equals(prefix+war),"war exit expected producer changed the original terminal route");
        return new ExpectedPostcondition(1,before,source,OrdinaryWarExitObservation.SCHEMA,
                List.of(new ExpectedInteger(new FieldKey("war_id"),BigInteger.valueOf(war)),new ExpectedBoolean(new FieldKey("war_absence_observed"),true)));
    }
    private static Optional<PlanningReadReceipt> postRead(RootRuntimeContext context,ArmyOrdinaryPairedQuotes.Producers producers,
            NativeArmyOrdinaryEffects.Query query,ActionCommand original,Complete after) {
        try {
            Session same=context.borrowedSession();context.writer().requireSession(same);
            StrictJson.require(after.source().equals(original.source())&&after.sessionId().equals(original.sessionId())
                    &&after.identity().game().equals(original.before().game()),"Army independent material query crossed its original Game/source/session");
            Instant deadline=ActionObservationWindow.deadline(original);
            if(query.kind()==NativeArmyOrdinaryEffects.ReadKind.OCCUPATION) {
                var call=new ArmyCalls.War(PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1,revision(after),BigInteger.valueOf(query.warId()));
                var selection=new ArmyWarReads.Selection(call,new ArmyRetreatFrames.Current(after,deadline),Optional.empty());
                return known(producers.wars().read(same,context.readCatalog(),selection));
            }
            var call=new ArmyCalls.Frame(PublicMethod.QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1,revision(after));
            var selection=new ArmyClosedReadContracts.Selection(call,new ArmyTypes.Context(after.identity(),after.source(),after.sessionId(),deadline));
            var contract=producers.closed().issue(context.readCatalog(),selection);
            return known(context.reads().read(same,contract,producers.closed().request(selection)));
        } catch(IOException unavailable) {throw new UncheckedIOException("original same-writer Army independent material query unavailable",unavailable);}
    }
    private static <T> Optional<PlanningReadReceipt> known(PlanningReadResult<T> result) {
        return result instanceof PlanningReadResult.Known<T> value?Optional.of(value.receipt()):Optional.empty();
    }
    private static ArmyCalls.Revision revision(Complete frame) {return new ArmyCalls.Revision(new ArmyTypes.Present<>(frame.identity().frame().revision()));}
    static void requireDefaultRaise(BigInteger actualActor,ArmyClosedReads.Observation result) {
        StrictJson.require(result instanceof ArmyClosedReads.DefaultRaise,"default raise quote returned another native domain");
        var raise=(ArmyClosedReads.DefaultRaise)result;
        StrictJson.require(BigInteger.valueOf(raise.actor()).equals(actualActor)&&raise.legalityReady()
                &&raise.legal() instanceof ArmyTypes.Present<Boolean> legal&&legal.value()&&raise.reserveReady()
                &&raise.soldiers() instanceof ArmyTypes.Present<Integer> reserve&&reserve.value()>0,
                "default raise lacks actual native legality or a nonempty observed reserve");
    }
    private static ActionReceipt commander(RootRuntimeContext context,CommanderBindings commander,Session same,
            ArmyCalls.AssignCommander input,ArmyTypes.Context source,String actionId) {
        try {
            context.writer().requireSession(same);
            ActionCommand command=context.collector().withOwnedPlanning(same,context.collector().identity(),source.deadline(),(request,lease)->{
                StrictJson.require(request.before().equals(source.before())&&request.source().equals(source.source())
                        &&request.sessionId().equals(source.sessionId()),"public commander full planning request changed its selected original frame");
                var result=commander.read(request,input.army().value(),context.readCatalog(),same);
                if(!(result instanceof PlanningReadResult.Known<CommanderObservationCollector.Observation> known))
                    throw new IllegalStateException("actual selected Army commander query is unavailable");
                var observed=known.value().observed().normalized();
                StrictJson.require(observed.army().value()==input.army().value()&&observed.collectionComplete()
                        &&observed.nativeArmy().value()!=null&&observed.owner().value()!=null
                        &&BigInteger.valueOf(observed.owner().value().value()).equals(source.playerId())
                        &&observed.dateRaw().equals(source.dateRaw())
                        &&observed.rows().stream().filter(row->row.character().value()!=null&&row.character().value().value()==input.character().value()
                                &&row.available()&&row.eligibilityObservable()&&Boolean.TRUE.equals(row.canAssign().value())).count()==1,
                        "selected commander lacks complete current native parent identity or final eligibility");
                var arguments=new CommanderAssignmentPostcondition.Arguments(BigInteger.valueOf(input.army().value()),BigInteger.valueOf(input.character().value()),
                        BigInteger.valueOf(observed.nativeArmy().value().value()),source.playerId(),source.dateRaw());
                return commander.assignment(request,arguments,context.bindings(),actionId);
            });
            // The collector callback has returned and its native/Driver freeze is closed before submission.
            return context.actions().execute(same,command);
        } catch(IOException unavailable) {throw new UncheckedIOException("actual public commander full-planning delegate unavailable",unavailable);}
    }
    private static ActionReceipt mercenary(RootRuntimeContext context,Session same,ArmyCalls.Hire input,ArmyTypes.Context source,String actionId) {
        try {
            context.writer().requireSession(same);
            var finance=context.finance();
            StrictJson.require(finance.game().equals(source.before().game())&&finance.source().equals(source.source())
                    &&finance.sessionId().equals(source.sessionId()),"public mercenary delegate is not the identical current FinanceRuntimeServices");
            ActionCommand command=context.collector().withOwnedPlanning(same,context.collector().identity(),source.deadline(),(request,lease)->{
                StrictJson.require(request.before().equals(source.before())&&request.source().equals(source.source())
                        &&request.sessionId().equals(source.sessionId()),"public mercenary full planning request changed its selected original frame");
                return finance.policies().publicHire(same,request,BigInteger.valueOf(input.id().value()),actionId);
            });
            StrictJson.require(command.actionId().equals(actionId)&&command.operation().value().equals("hire-mercenary-v1"),
                    "the original finance producer changed the public hire command identity");
            return context.actions().execute(same,command);
        } catch(IOException unavailable) {throw new UncheckedIOException("actual complete finance public hire delegate unavailable",unavailable);}
    }
    private static final class FinalGates implements ArmyOrdinaryActionPreparation.FinalGates {
        private final RootRuntimeContext context;private final ArmyClosedReadContracts closed;private final Duration timeout;
        private FinalGates(RootRuntimeContext context,ArmyClosedReadContracts closed,Duration timeout) {
            this.context=context;this.closed=closed;this.timeout=timeout;
        }
        @Override public void verify(Complete frame,ArmyOrdinaryActionArguments args,NativeRequest primitive) {
            throw new IllegalStateException("Army final native gate requires the original held writer Session");
        }
        @Override public void verify(Session same,Complete frame,ArmyOrdinaryActionArguments args,NativeRequest primitive) {
            try {
                context.writer().requireSession(same);
                context.collector().current(same,frame.identity(),context.clock().instant().plus(timeout),lease->{
                    StrictJson.require(lease.frame().fullBindingSha256().equals(frame.fullBindingSha256())
                            &&lease.frame().originalEvidence().equals(frame.originalEvidence()),"final Army gate changed its full actual Native/Driver binding");
                    var call=ArmyCallCodec.decode(PublicMethod.valueOf(args.kind().name()),args.publicArguments());
                    var selected=new ArmyTypes.Context(frame.identity(),frame.source(),frame.sessionId(),context.clock().instant().plus(timeout));
                    StrictJson.require(ArmyOrdinaryActionPreparation.primitive(call,selected,List.of()).equals(primitive),
                            "remaining Army final gate differs from its exact original typed primitive");
                    var archive=context.archive().withSession(same);
                    for(var ref:args.preflightReads()) {
                        var read=archive.loadRead(ref);NativeRecordedEvidenceVerifier.requireRead(read,archive);ArmyOrdinaryPreflight.bind(read,frame);
                    }
                    if(args.kind()==Kind.SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1) {
                        StrictJson.require(args.preflightReads().isEmpty(),"original regular MAA submission has no invented final quotation prerequisite");
                        StrictJson.require(frame.identity().frame().identity().player().equals(BigInteger.valueOf(29829)),"native regular personal Create provider only supports actual Robert29829");
                        RegularMaaPrivatePermission.validate(primitive);
                        // Native permission still invokes the Root's actual exact-build/source verifier at dispatch.
                        // Queue acceptance remains Pending; no creation/payment/usable-troop authority is granted.
                    }
                    if(args.kind()==Kind.RAISE_TROOPS_DEFAULT) {
                        StrictJson.require(args.preflightReads().size()==1,"default raise requires its one original complete native quote");
                        var read=archive.loadRead(args.preflightReads().getFirst());
                        var quoteInput=new ArmyCalls.Frame(PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1,revision(frame));
                        var quoteContext=new ArmyTypes.Context(frame.identity(),frame.source(),frame.sessionId(),read.request().deadline());
                        var contract=closed.issue(context.readCatalog(),new ArmyClosedReadContracts.Selection(quoteInput,quoteContext));
                        var result=contract.replay(read);
                        requireDefaultRaise(frame.identity().frame().identity().player(),result);
                    }
                    context.collector().requireHeldFrame(same,lease.frame());return null;
                });
            } catch(IOException unavailable) {throw new UncheckedIOException("actual remaining Army final gate unavailable",unavailable);}
        }
    }
}
