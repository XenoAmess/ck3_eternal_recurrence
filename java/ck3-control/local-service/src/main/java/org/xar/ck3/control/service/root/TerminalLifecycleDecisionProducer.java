package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.io.IOException;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.lifecycle.*;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.application.session.SessionPorts.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Existing lifecycle policy at the real terminal decision boundary. No planner, native mutation or ledger commit. */
public final class TerminalLifecycleDecisionProducer {
    private static final String SETTLEMENT_CAPABILITY="game.state.xar-one-life-settlement";
    private final ContinuityWriter writer;
    private final RootLifecycleAuthority terminal;
    private final ActionSnapshotReader actions;
    private final LifecycleComposites lifecycle;
    private final LifecycleComposites.ActualSeeds actualSeeds;
    private SeedStore seeds()throws IOException {
        SeedStore actual=actualSeeds.require();if(actual==null)throw new IOException("actual admitted terminal SeedStore is unavailable");return actual;
    }
    private final CheckpointFiles files;
    private final RootNaturalSuccessionOriginals natural;
    private final Clock clock;
    private final Duration actionBudget;
    private enum LifeCompletion { SCORED, UNAVAILABLE }
    /** Privately joined immutable canonical terminal DATA; no action, episode or import grant. */
    public static final class CanonicalTerminal {
        private final ActionReceipt receipt;private final OpportunityJson.Obj result;
        private final ExactRef before,row;private final List<ExactRef> evidence;
        private CanonicalTerminal(ActionReceipt receipt,OpportunityJson.Obj result,ExactRef before,ExactRef row,List<ExactRef> evidence){
            this.receipt=receipt;this.result=result;this.before=before;this.row=row;this.evidence=List.copyOf(new LinkedHashSet<>(evidence));
        }
        public ActionReceipt actualReceipt(){return receipt;}
        public OpportunityJson.Obj resultObj(){return result;}
        public ExactRef driverBeforeExactRef(){return before;}
        public ExactRef terminalRowExactRef(){return row;}
        public List<ExactRef> evidenceList(){return evidence;}
    }
    /** Same live terminal scope, exact original parent/row/proof; caller mutates only after this callback ends. */
    public Optional<CanonicalTerminal> canonicalTerminal(ContinuityStorePort.Session same,RootLifecycleAuthority.Lease observed,Instant deadline)throws IOException {
        writer.requireSession(same);Objects.requireNonNull(observed);Objects.requireNonNull(deadline);
        return terminal.current(same,observed.identity(),deadline,actual->{
            require(actual==observed,"canonical terminal join requires this actual Root observation scope");actual.assertCurrent(same);
            var result=joinCanonicalDeath(same,actual.snapshot().facts(),canonical(same),actual.identity(),new ArrayList<>(references(actual.identity())));
            actual.assertCurrent(same);return result;
        });
    }

    public TerminalLifecycleDecisionProducer(ContinuityWriter writer,RootLifecycleAuthority terminal,ActionSnapshotReader actions,
            LifecycleComposites lifecycle,SeedStore seeds,CheckpointFiles files,RootNaturalSuccessionOriginals natural,
            Clock clock,Duration actionBudget) {
        this(writer,terminal,actions,lifecycle,fixedSeeds(seeds),files,natural,clock,actionBudget);
    }
    public TerminalLifecycleDecisionProducer(ContinuityWriter writer,RootLifecycleAuthority terminal,ActionSnapshotReader actions,
            LifecycleComposites lifecycle,LifecycleComposites.ActualSeeds seeds,CheckpointFiles files,RootNaturalSuccessionOriginals natural,
            Clock clock,Duration actionBudget) {
        this.writer=Objects.requireNonNull(writer);this.terminal=Objects.requireNonNull(terminal);this.actions=Objects.requireNonNull(actions);
        this.lifecycle=Objects.requireNonNull(lifecycle);this.actualSeeds=Objects.requireNonNull(seeds);this.files=Objects.requireNonNull(files);
        this.natural=Objects.requireNonNull(natural);this.clock=Objects.requireNonNull(clock);this.actionBudget=Objects.requireNonNull(actionBudget);
        require(!actionBudget.isNegative()&&!actionBudget.isZero()&&actionBudget.compareTo(Duration.ofMinutes(5))<=0,"finite original lifecycle action budget required");
    }
    private static LifecycleComposites.ActualSeeds fixedSeeds(SeedStore seeds){SeedStore actual=Objects.requireNonNull(seeds);return ()->actual;}
    /** Root calls this before ordinary observations, including the interval after Driver publication and before parent settlement. */
    public Optional<TerminalReady> pending(ContinuityStorePort.Session same,SessionIdentity owner)throws IOException {
        writer.requireSession(same);Objects.requireNonNull(owner);require(owner.machineId().equals(same.head().state().machineId()),"pending lifecycle observation crossed the actual writer machine");var snapshot=canonical(same);
        var original=firstUnresolved(snapshot.actions(),owner,Optional.empty());
        if(original.isEmpty()||!(original.orElseThrow().command().origin() instanceof CommandOrigin.LifecycleTerminal))return Optional.empty();
        var receipt=original.orElseThrow();var identity=receipt.command().lifecycleBefore();var evidence=references(identity);
        try {
            var retained=lifecycle.retainedReconciliation(same,receipt);
            if(retained.isPresent())return Optional.of(new TerminalReady(retained.orElseThrow(),new TerminalReconciliation(receipt.command().actionId())));
            return Optional.of(new TerminalReady(identity,new TerminalBlocked("canonical lifecycle parent is unresolved but its original private publication custody is unavailable; original scope is diagnostic only",evidence)));
        }catch(IOException|IllegalArgumentException|IllegalStateException failure) {
            return Optional.of(new TerminalReady(identity,new TerminalBlocked("original lifecycle completion source cannot be revalidated: "+failure.getMessage(),evidence)));
        }
    }
    /** The live lease must belong to this exact Root authority. The returned command is only a candidate for the sole coordinator. */
    public TerminalReady decide(ContinuityStorePort.Session same,RootLifecycleAuthority.Lease observed,Instant deadline)throws IOException {
        writer.requireSession(same);Objects.requireNonNull(observed);Objects.requireNonNull(deadline);
        return terminal.current(same,observed.identity(),deadline,actual->{
            require(actual==observed,"detached or foreign lifecycle observation is not this Root decision scope");actual.assertCurrent(same);
            var evidence=new ArrayList<>(references(actual.identity()));evidence.add(actual.originalHeartbeat());evidence.add(actual.originalSemantic());
            TerminalDecision result;
            try { result=choose(same,actual,deadline,evidence); }
            catch(IOException|IllegalArgumentException|IllegalStateException|ArithmeticException failure) {result=blocked("actual terminal source is unavailable: "+failure.getMessage(),evidence);}
            actual.assertCurrent(same);return new TerminalReady(actual.identity(),result);
        });
    }
    private TerminalDecision choose(ContinuityStorePort.Session same,RootLifecycleAuthority.Lease actual,Instant deadline,List<ExactRef> evidence)throws IOException {
        var identity=actual.identity();var snapshot=actual.snapshot();var owner=new SessionIdentity(identity.machineId(),identity.game(),identity.sessionId());
        var canonical=canonical(same);var unresolved=firstUnresolved(canonical.actions(),owner,Optional.of(snapshot.source()));
        if(unresolved.isPresent()) {
            var command=unresolved.orElseThrow().command();
            if(command.origin() instanceof CommandOrigin.LifecycleTerminal original) {
                if(original.identity().sameSession(identity))return new TerminalReconciliation(command.actionId());
                return blocked("an unresolved lifecycle parent belongs to another original episode; use retained original completion scope",evidence);
            }
            if(command.origin() instanceof CommandOrigin.Gameplay original
                    &&original.before().frame().episodeRunId().equals(identity.subject().episodeRunId())
                    &&original.before().frame().identity().player().equals(identity.subject().characterId()))return new TerminalReconciliation(command.actionId());
            return blocked("original action "+command.actionId()+" is unresolved outside this terminal subject; no new lifecycle command is permitted",evidence);
        }
        require(identity.subject().characterId().equals(snapshot.facts().driver().session().actorId())
                &&identity.subject().episodeRunId().equals(snapshot.facts().driver().session().episodeRunId())
                &&identity.subject().episodeEpoch()==snapshot.facts().stamp().episodeEpoch()
                &&identity.subject().driverVersion()==snapshot.facts().stamp().driverVersion(),"actual terminal policy crossed its full old Driver subject");
        String policy=LifecycleReducer.lifecycle(snapshot.facts().driver());
        if(policy.equals("ordinary_campaign_succession")) {
            require(snapshot.facts().driver().campaignGoal() instanceof DriverStateSnapshot.Value,"ordinary succession requires its actual persisted campaign goal");
            GoalCodec.decodeGoal(((DriverStateSnapshot.Value)snapshot.facts().driver().campaignGoal()).json());
            return natural(same,actual,deadline,evidence);
        }
        require(policy.equals("rogue_one_life"),"unbound lifecycle policy cannot choose a terminal operation");
        Optional<LifeCompletion> completed=canonicalDeath(same,snapshot.facts(),canonical,identity,evidence);
        if(completed.isPresent()) {
            if(completed.orElseThrow()==LifeCompletion.UNAVAILABLE)return blocked("the original death-terminal completed without settlement support; do not issue it again",evidence);
            LifecycleReducer.requireScoredTerminal(snapshot.facts().driver());
            if(identity.terminalReason()==LifecycleIdentity.TerminalReason.CHANGED)return natural(same,actual,deadline,evidence);
            if(!snapshot.paused()||!snapshot.mapReady())return new TerminalWait("scored original life awaits the actual paused map before immutable-seed replacement");
            SeedAdoption read=seeds().read();
            if(!(read instanceof SeedAdoption.Available available)) {
                if(read instanceof SeedAdoption.Unavailable absent)evidence.addAll(absent.evidence());
                if(read instanceof SeedAdoption.Unknown unknown)evidence.addAll(unknown.evidence());
                return blocked("original immutable first-life seed is unavailable: "+read,evidence);
            }
            available.artifact().requireCurrent(files);evidence.add(available.artifact().save().reference());evidence.add(available.artifact().metadata().reference());
            return selected(identity,snapshot.source(),LifecycleExpectedPostcondition.Operation.START_NEXT_EPISODE,deadline);
        }
        if(!actual.bridgeCapabilities().contains(SETTLEMENT_CAPABILITY))return blocked("actual hello lacks the one-life settlement capability; no scored death or next episode is authorized",evidence);
        var settlement=LifecycleComposites.settlementFromSnapshot(snapshot);
        if(settlement.isEmpty())return new TerminalWait("await the actual original subject's native settlement; no death command has been issued");
        require(settlement.orElseThrow().sourceCharacterId().equals(identity.subject().characterId()),"native settlement belongs to another original episode subject");
        require(snapshot.facts().auxiliary().members().containsKey("one_life_strategy"),"original one-life strategy presence or null is unavailable");
        var strategy=snapshot.facts().auxiliary().get("one_life_strategy");
        if(strategy!=OpportunityJson.Nil.INSTANCE){var object=OpportunityJson.object(strategy,"original one-life strategy");
            if(object.members().containsKey("episodes"))require(object.get("episodes") instanceof OpportunityJson.Arr,"original one-life strategy episodes are not an array");}
        return selected(identity,snapshot.source(),LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL,deadline);
    }
    private TerminalDecision natural(ContinuityStorePort.Session same,RootLifecycleAuthority.Lease actual,Instant deadline,List<ExactRef> evidence)throws IOException {
        var identity=actual.identity();
        if(identity.terminalReason()!=LifecycleIdentity.TerminalReason.CHANGED
                ||!(identity.currentPlayer() instanceof LifecycleIdentity.Character player)||!player.alive())
            return blocked("this policy has no actual distinct living played successor",evidence);
        if(!actual.snapshot().paused()||!actual.snapshot().mapReady())return new TerminalWait("actual natural successor awaits the paused ready map");
        var candidate=natural.inspectCandidate(actual);
        if(candidate.isEmpty())return blocked("no actual retained pre-clock GetPlayerHeir, original clock and independent predecessor-death candidate is available",evidence);
        var original=candidate.orElseThrow();
        require(BigInteger.valueOf(original.predecessor()).equals(identity.subject().characterId())
                &&BigInteger.valueOf(original.successor()).equals(player.characterId()),"actual natural candidate differs from old subject/current living actor");
        evidence.addAll(List.of(original.capture(),original.clockReceipt(),original.retainedDeath()));actual.assertCurrent(same);
        return selected(identity,actual.snapshot().source(),LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR,deadline);
    }
    /** This is a canonical result join, never a latest-row shape-to-success conversion. */
    private Optional<LifeCompletion> canonicalDeath(ContinuityStorePort.Session same,DriverSnapshotFacts.Known known,ActionJournal.Snapshot canonical,
            LifecycleIdentity current,List<ExactRef> evidence)throws IOException {
        return joinCanonicalDeath(same,known,canonical,current,evidence).map(joined->{
            String status=OpportunityJson.text(joined.resultObj().get("settlement_status"),"settlement_status");
            return switch(status){case "complete"->LifeCompletion.SCORED;case "settlement_unavailable"->LifeCompletion.UNAVAILABLE;
                default->throw new IllegalArgumentException("unknown original terminal settlement disposition");};
        });
    }
    /** A legacy ordinal joins only actual legacy coverage; canonical-only facts have no compatibility row to impersonate. */
    record LegacyActionCoverage(DriverSnapshotFacts.ActionRow action,DriverSnapshotFacts.LegacyHistoryRow source) { }
    static List<LegacyActionCoverage> legacyRowsAt(List<DriverSnapshotFacts.ActionRow> rows,long index) {
        Objects.requireNonNull(rows);org.xar.ck3.control.contracts.StrictJson.safe(index,1);
        var actual=new ArrayList<LegacyActionCoverage>();
        for(var row:List.copyOf(rows))if(row.coverageSource() instanceof DriverSnapshotFacts.LegacyHistoryRow legacy
                &&legacy.historyIndex()==index)actual.add(new LegacyActionCoverage(row,legacy));
        return List.copyOf(actual);
    }
    private Optional<CanonicalTerminal> joinCanonicalDeath(ContinuityStorePort.Session same,DriverSnapshotFacts.Known known,
            ActionJournal.Snapshot canonical,LifecycleIdentity current,List<ExactRef> evidence)throws IOException {
        var history=known.driver().commandHistory();
        for(int index=history.size()-1;index>=0;index--) {
            var entry=history.get(index);var row=DriverJson.object(entry.originalRow().json(),DriverJson.MAX_NATIVE_BYTES);
            if(!new OpportunityJson.Text("death-terminal").equals(row.get("command")))continue;
            require(OpportunityJson.bool(row.get("ok"),"ok"),"latest original death-terminal is not successful");
            var coverage=legacyRowsAt(known.actionRows(),entry.index());
            require(coverage.size()==1,"original terminal row lacks unique canonical action coverage");
            var covered=coverage.getFirst();var binding=covered.action();var originalRow=covered.source().originalRow();
            require(originalRow.bytes()==entry.originalRow().json().length
                    &&originalRow.sha256().equals(DriverJson.sha256(entry.originalRow().json())),"original terminal row binding differs");
            var pin=same.capturePin(originalRow,WriterContracts.MAX_PIN_BYTES);
            require(Arrays.equals(same.readPinned(pin,WriterContracts.MAX_PIN_BYTES),entry.originalRow().json()),"actual archived terminal row differs");
            var found=canonical.actions().stream().filter(value->value.command().actionId().equals(binding.actionId())).toList();
            require(found.size()==1,"original terminal row has no actual canonical parent");var receipt=found.getFirst();
            require(receipt.bodySha256().equals(binding.bodySha256())&&receipt.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED
                    &&receipt.state() instanceof ActionState.CompositeSettled settled&&settled.settlement() instanceof ActionState.LifecycleApplied,
                    "original terminal row does not carry a canonical applied lifecycle result");
            var proof=((ActionState.LifecycleApplied)((ActionState.CompositeSettled)receipt.state()).settlement()).proof();
            var origin=receipt.command().lifecycleBefore();
            require(proof.kind()==LifecycleTransitionProof.Kind.DEATH&&origin.sameSession(current),"scored terminal belongs to another old subject/episode");
            lifecycle.verifyRecorded(receipt.command(),proof,same.head());evidence.add(originalRow);evidence.addAll(proof.originalEvidence());
            var result=OpportunityJson.object(row.get("result"),"death result");
            require(DriverJson.object(proof.encodedResult(),LifecycleProofCodec.MAX_RESULT_BYTES).equals(result),"canonical death proof and complete Driver result differ");
            ExactRef before=origin.evidence().originalDriver();var beforePin=same.capturePin(before,WriterContracts.MAX_PIN_BYTES);
            var originalBefore=DriverStateSnapshot.decodeComplete(same.readPinned(beforePin,WriterContracts.MAX_PIN_BYTES));same.verifyPin(beforePin);
            require(originalBefore.session().episodeRunId().equals(origin.subject().episodeRunId())
                    &&originalBefore.session().actorId().equals(origin.subject().characterId()),"original terminal before-Driver crossed its actual old subject");
            evidence.add(before);
            return Optional.of(new CanonicalTerminal(receipt,result,before,originalRow,evidence));
        }
        require(canonical.actions().stream().noneMatch(value->value.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED&&value.command().origin() instanceof CommandOrigin.LifecycleTerminal terminal
                &&terminal.identity().sameSession(current)&&value.command().operation().equals(LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL.key())),
                "canonical terminal parent exists without its actual complete Driver row; never issue another death command");
        return Optional.empty();
    }
    private ActionJournal.Snapshot canonical(ContinuityStorePort.Session same)throws IOException {
        var snapshot=actions.withFrozen(same,lease->{lease.assertCurrent();return lease.snapshot();});
        require(snapshot.headSha256().equals(same.head().digest()),"terminal decision did not borrow the current canonical action snapshot");return snapshot;
    }
    static Optional<ActionReceipt> firstUnresolved(List<ActionReceipt> actual,SessionIdentity owner,Optional<G2Source> source) {
        return actual.stream().filter(value->!value.settled()&&value.command().origin().machineId().equals(owner.machineId())
                &&value.command().origin().game().equals(owner.game())&&value.command().sessionId().equals(owner.sessionId())
                &&source.map(expected->expected.equals(value.command().source())).orElse(true)).min(Comparator.comparingLong(ActionReceipt::sequence));
    }
    private TerminalDecision selected(LifecycleIdentity identity,G2Source source,LifecycleExpectedPostcondition.Operation operation,Instant deadline) {
        return new TerminalAction(command(identity,source,operation,actionDeadline(deadline)));
    }
    private Instant actionDeadline(Instant caller){Instant local=clock.instant().plus(actionBudget);Instant until=caller.isBefore(local)?caller:local;require(clock.instant().isBefore(until),"original lifecycle caller deadline expired");return until;}
    static ActionCommand command(LifecycleIdentity identity,G2Source source,LifecycleExpectedPostcondition.Operation operation,Instant deadline) {
        var values=List.<ExpectedValue>of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"),false),
                new ExpectedBoolean(new FieldKey("timeline.advance_verified"),false),new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"),false));
        var expected=new LifecycleExpectedPostcondition(identity,source,"xar.java.lifecycle-composite-result/v1",operation,values);
        return new ActionCommand(ActionIds.forDecision(identity.sessionId(),identity,operation.key().value()),new CommandOrigin.LifecycleTerminal(identity),source,
                identity.sessionId(),operation.key(),new OpportunityJson.Obj(Map.of("expected_revision",new OpportunityJson.IntegerValue(identity.frame().revision()))),
                new CommandExpectation.LifecycleTerminal(expected),new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),deadline);
    }
    private static TerminalBlocked blocked(String reason,List<ExactRef> evidence){return new TerminalBlocked(reason,List.copyOf(new LinkedHashSet<>(evidence)));}
    private static List<ExactRef> references(LifecycleIdentity identity){var rows=new ArrayList<>(identity.supportingEvidence());rows.add(identity.nativeEvidence());rows.add(identity.capabilityEvidence());return List.copyOf(new LinkedHashSet<>(rows));}
}
