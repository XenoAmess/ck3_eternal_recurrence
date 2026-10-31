package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.EnumSet;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessment;

/** Sole current owned-submission inventory. Native debt/loan/refund terms and unreceived funds are separate unqualified facts. */
public final class CanonicalFundingPending {
    public static final String SCHEMA="xar.java.canonical-owned-funding-inventory/v2";
    private static final String EMPTY_ACTION_DIGEST=ActionCodec.sha256(new byte[0]);
    private static final Set<FinanceStatePort.Domain> REQUIRED=Set.of(FinanceStatePort.Domain.CONSTRUCTION,FinanceStatePort.Domain.FACTION_GIFT,
            FinanceStatePort.Domain.MERCENARY,FinanceStatePort.Domain.FEAST,FinanceStatePort.Domain.FIRST_HEIR_MARRIAGE,
            FinanceStatePort.Domain.CHILD_MARRIAGE,FinanceStatePort.Domain.CHILD_DEFAULT_MARRIAGE);
    public enum Phase { INTENT_ABANDONED, INTENT_DURABLE, SUBMITTING, ACKNOWLEDGED, UNKNOWN, COMPOSITE_RUNNING, COMPOSITE_UNKNOWN, SETTLED, REJECTED_BEFORE_DISPATCH, COMPOSITE_SETTLED,
        PHYSICAL_SUBMITTING, PHYSICAL_UNKNOWN, PHYSICAL_COMPLETED, PHYSICAL_NOT_POSTED;
        /** Only terminality of an owned submission. Physical completion carries no funding or Game-effect credit. */
        public boolean settled(){return this==INTENT_ABANDONED||this==SETTLED||this==REJECTED_BEFORE_DISPATCH||this==COMPOSITE_SETTLED
                ||this==PHYSICAL_COMPLETED||this==PHYSICAL_NOT_POSTED;}
    }
    public enum Scope { OWNED_SUBMISSION_INVENTORY }
    public enum OwnedState { CLEAR, UNRESOLVED }
    public enum NativeFundingCoverage { COMPLETE_DEBT_LOAN_REFUND_UNQUALIFIED }
    public record BodyFact(FinanceStatePort.Domain domain,ExactRef original,ExactRef decoderSource,FinanceStatePort.Pending pending) {
        public BodyFact {Objects.requireNonNull(domain);requiredRef(original);requiredRef(decoderSource);Objects.requireNonNull(pending);}
    }
    public record FamilyFact(String id,ReadContract.GuardMode guardMode,Optional<String> requiredCapability,
            ExactRef implementationSource,ExactRef decoderSource,ExactRef verifierSource) {
        public FamilyFact {StrictJson.text(id);Objects.requireNonNull(guardMode);Objects.requireNonNull(requiredCapability);requiredCapability.ifPresent(StrictJson::text);
            requiredRef(implementationSource);requiredRef(decoderSource);requiredRef(verifierSource);}
    }
    public record ActionFact(String actionId,OperationKey operation,String bodySha256,Phase phase,ExactRef originalReceipt) {
        public ActionFact {StrictJson.text(actionId);Objects.requireNonNull(operation);digest(bodySha256);Objects.requireNonNull(phase);requiredRef(originalReceipt);}
    }
    /** DATA only. Its constructor and JSON decoder cannot mint a live Observed or current writer qualification. */
    public record SourceEvidence(ObservationIdentity current,G2Source source,String sessionId,ExactRef canonicalHead,long ledgerSequence,String headSha256,
            List<BodyFact> bodies,List<ExecutableStepBindings.InstalledStep> installed,List<FamilyFact> families,
            long canonicalActionCount,String canonicalActionInventorySha256,List<ActionFact> unresolvedActions) {
        public SourceEvidence {
            Objects.requireNonNull(current);Objects.requireNonNull(source);StrictJson.text(sessionId);requiredRef(canonicalHead);StrictJson.safe(ledgerSequence,0);digest(headSha256);
            require(current.machineId().equals(source.machineId()),"funding current source machine differs");
            bodies=List.copyOf(bodies);installed=List.copyOf(installed);families=List.copyOf(families);unresolvedActions=List.copyOf(unresolvedActions);
            StrictJson.safe(canonicalActionCount,0);digest(canonicalActionInventorySha256);
            require(canonicalActionCount>=unresolvedActions.size()&&(canonicalActionCount!=0||EMPTY_ACTION_DIGEST.equals(canonicalActionInventorySha256)),"canonical action reduction summary differs from its complete count");
            require(bodies.size()<=FinanceStatePort.Domain.values().length&&installed.size()<=8192&&families.size()<=256&&unresolvedActions.size()<=65536,"bounded complete funding source inventory required");
            var domains=EnumSet.noneOf(FinanceStatePort.Domain.class);for(var body:bodies)require(domains.add(body.domain()),"duplicate funding body domain");
            require(domains.containsAll(REQUIRED),"all actual owned gold-spending domain bodies must be registered and present");
            var operations=new HashSet<OperationKey>();for(var step:installed)require(operations.add(step.operation()),"duplicate installed funding inventory operation");
            require(installed.stream().anyMatch(step->step.kind()==ExecutableStepBindings.Kind.ACTION&&step.operation().equals(OrdinaryFinancePolicies.MERCENARY))
                    &&installed.stream().anyMatch(step->step.kind()==ExecutableStepBindings.Kind.ACTION&&step.operation().equals(OrdinaryFinancePolicies.GIFT)),"actual finance action registrations are absent");
            var familyIds=new HashSet<String>();for(var family:families)require(familyIds.add(family.id()),"duplicate actual Root action family");
            var actionIds=new HashSet<String>();for(var action:unresolvedActions)require(!action.phase().settled()&&actionIds.add(action.actionId()),"only unique actual unresolved canonical action originals belong in the bounded subset");
        }
        public Scope scope(){return Scope.OWNED_SUBMISSION_INVENTORY;}
        public NativeFundingCoverage nativeFundingCoverage(){return NativeFundingCoverage.COMPLETE_DEBT_LOAN_REFUND_UNQUALIFIED;}
        public long unreceivedFundingCreditedRaw(){return 0;}
        public OwnedState ownedState(){return CanonicalFundingPending.ownedState(this);}
    }
    public sealed interface Result permits Observed,Unavailable { }
    /** Only this actual same-writer reader mints current eligibility; pure historical evidence is insufficient. */
    public static final class Observed implements Result {
        private final SourceEvidence evidence;
        private Observed(SourceEvidence evidence){this.evidence=Objects.requireNonNull(evidence);}
        public SourceEvidence sourceEvidence(){return evidence;}
        public OwnedState ownedState(){return evidence.ownedState();}
        public EmergencyFinancingAssessment.PendingObservation pending(){return CanonicalFundingPending.pending(evidence);}
    }
    public record Unavailable(String reason) implements Result {public Unavailable{StrictJson.text(reason);}}
    private final ActionSnapshotReader actions;private final Path writerLock;private final FinanceStatePort state;
    private final EnumMap<FinanceStatePort.Domain,FinanceStatePort.ReaderBinding> readers=new EnumMap<>(FinanceStatePort.Domain.class);
    private final Supplier<RootExecutableBindings> bindings;private final Function<Session,ActionPorts.OutcomeArchive> archives;
    private final GameGeneration game;private final G2Source source;private final String sessionId;
    public CanonicalFundingPending(ActionSnapshotReader actions,Path writerLock,FinanceStatePort state,List<FinanceStatePort.ReaderBinding> actualReaders,
            Supplier<RootExecutableBindings> actualBindings,Function<Session,ActionPorts.OutcomeArchive> actualArchives,
            GameGeneration game,G2Source source,String sessionId) {
        this.actions=Objects.requireNonNull(actions);this.writerLock=Objects.requireNonNull(writerLock).toAbsolutePath().normalize();this.state=Objects.requireNonNull(state);
        for(var reader:List.copyOf(actualReaders))require(readers.putIfAbsent(reader.domain(),reader)==null,"duplicate actual finance reader registration");
        bindings=Objects.requireNonNull(actualBindings);archives=Objects.requireNonNull(actualArchives);this.game=Objects.requireNonNull(game);this.source=Objects.requireNonNull(source);this.sessionId=StrictJson.text(sessionId);
    }
    public Result read(Session same,PlanningRequest request)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(request);same.requireWriter(writerLock);
        try {
            require(game.equals(request.before().game())&&source.equals(request.source())&&sessionId.equals(request.sessionId())
                    &&Instant.now().isBefore(request.deadline()),"funding read crossed its current physical Game/source/session/deadline");
            var start=same.head();var persisted=same.persistedHead();
            if(!readers.keySet().containsAll(REQUIRED))return new Unavailable("actual owned-spending reader registrations are incomplete");
            var originalState=state.read(same,request);
            if(!(originalState instanceof FinanceStatePort.Known known))return new Unavailable("actual current finance body inventory is unavailable: "+((FinanceStatePort.Missing)originalState).reason());
            var retained=known.snapshot();require(retained.head().canonicalHead().equals(persisted),"funding body inventory crossed the actual canonical head");
            var bodies=new ArrayList<BodyFact>();
            for(var entry:readers.entrySet()) {
                var ledger=retained.ledger(entry.getKey());if(ledger.isEmpty())return new Unavailable("actual registered spending body unavailable: "+entry.getKey());
                var body=ledger.orElseThrow();bodies.add(new BodyFact(entry.getKey(),body.document().original(),entry.getValue().definitionSource(),body.pending()));
            }
            var root=Objects.requireNonNull(bindings.get());require(root.frozen(),"funding inventory needs the actual frozen Root catalog");
            root.requireCompleteArchiveCoverage();
            var installed=root.installed();var families=familyFacts(root);var archive=Objects.requireNonNull(archives.apply(same));
            var evidence=actions.withFrozen(same,lease->{
                var snapshot=lease.snapshot();require(snapshot.headSha256().equals(start.digest())&&snapshot.actions().equals(retained.head().actualActionReceipts()),"funding full canonical action snapshot differs from the actual finance source");
                var unresolved=new ArrayList<ActionFact>();var inventory=sha256();
                for(var receipt:snapshot.actions()) {
                    ExactRef original=archive.receiptReferenceOf(receipt);require(receipt.equals(archive.loadReceipt(original)),"actual funding canonical receipt differs from its immutable archive");
                    var fact=new ActionFact(receipt.command().actionId(),receipt.command().operation(),receipt.bodySha256(),phase(receipt.state()),original);
                    byte[] encoded=encode(actionJson(fact));inventory.update(java.nio.ByteBuffer.allocate(4).putInt(encoded.length).array());inventory.update(encoded);
                    if(!fact.phase().settled())unresolved.add(fact);
                }
                lease.assertCurrent();return new SourceEvidence(request.before(),source,sessionId,persisted,snapshot.ledgerSequence(),snapshot.headSha256(),bodies,installed,families,
                        snapshot.actions().size(),java.util.HexFormat.of().formatHex(inventory.digest()),unresolved);
            });
            for(var body:evidence.bodies()){verify(same,body.original());verify(same,body.decoderSource());}
            for(var step:installed){verify(same,step.implementationSource());verify(same,step.decoderSource());}
            for(var family:families){verify(same,family.implementationSource());verify(same,family.decoderSource());verify(same,family.verifierSource());}
            require(root==bindings.get()&&installed.equals(root.installed())&&families.equals(familyFacts(root))
                    &&same.head().digest().equals(start.digest())&&same.persistedHead().equals(persisted)&&Instant.now().isBefore(request.deadline()),"actual funding inventory changed during same-writer qualification");
            encodeEvidence(evidence);return new Observed(evidence);
        }catch(IllegalArgumentException|IllegalStateException failure){return new Unavailable("actual owned funding inventory rejected: "+failure.getMessage());}
    }
    /** The sole pure reducer. CLEAR proves only the complete owned submission inventory, never funding receipt or native debt completeness. */
    public static EmergencyFinancingAssessment.PendingObservation pending(SourceEvidence evidence) {
        return ownedState(evidence)==OwnedState.CLEAR?new EmergencyFinancingAssessment.NoPendingAction():new EmergencyFinancingAssessment.PendingUnavailable();
    }
    /** The old emergency DTO has no generic/mercenary funding kind: blocked originals stay typed here instead of receiving an invented loan identity. */
    public static OwnedState ownedState(SourceEvidence evidence) {
        Objects.requireNonNull(evidence);return !evidence.unresolvedActions().isEmpty()
                ||evidence.bodies().stream().anyMatch(body->body.pending()!=FinanceStatePort.Pending.CLEAR)?OwnedState.UNRESOLVED:OwnedState.CLEAR;
    }
    /** Pure classification of original canonical state DATA; this cannot mint current Observed inventory. */
    public static Phase phase(ActionState state) {
        return switch(state) {
            case ActionState.IntentAbandoned ignored->Phase.INTENT_ABANDONED;case ActionState.IntentDurable ignored->Phase.INTENT_DURABLE;case ActionState.Submitting ignored->Phase.SUBMITTING;
            case ActionState.AckReceived ignored->Phase.ACKNOWLEDGED;case ActionState.Unknown ignored->Phase.UNKNOWN;
            case ActionState.CompositeRunning ignored->Phase.COMPOSITE_RUNNING;case ActionState.CompositeUnknown ignored->Phase.COMPOSITE_UNKNOWN;
            case ActionState.Settled ignored->Phase.SETTLED;case ActionState.RejectedBeforeDispatch ignored->Phase.REJECTED_BEFORE_DISPATCH;
            case ActionState.CompositeSettled ignored->Phase.COMPOSITE_SETTLED;
            case PhysicalActionState physical->switch(physical.phase()) {
                case SUBMITTING->Phase.PHYSICAL_SUBMITTING;case UNKNOWN->Phase.PHYSICAL_UNKNOWN;
                case COMPLETED->Phase.PHYSICAL_COMPLETED;case NOT_POSTED->Phase.PHYSICAL_NOT_POSTED;
            };
        };
    }
    private static List<FamilyFact> familyFacts(RootExecutableBindings root) {
        return root.families().stream().map(family->new FamilyFact(family.id(),family.guardMode(),family.requiredCapability(),family.implementationSource(),family.decoderSource(),family.verifierSource()))
                .sorted(java.util.Comparator.comparing(FamilyFact::id)).toList();
    }
    private static void verify(Session same,ExactRef original)throws IOException {var pin=same.capturePin(original,StrictJson.EXPLICIT_MAX_BYTES);same.verifyPin(pin);}
    private static void requiredRef(ExactRef ref){Objects.requireNonNull(ref);require(ref.bytes()>0,"actual nonempty original source required");}
    private static void digest(String value){require(value!=null&&value.matches("[0-9a-f]{64}"),"canonical SHA256 required");}
    private static java.security.MessageDigest sha256(){try{return java.security.MessageDigest.getInstance("SHA-256");}catch(java.security.NoSuchAlgorithmException impossible){throw new IllegalStateException("required SHA-256 unavailable",impossible);}}
    private static Obj actionJson(ActionFact action){return obj("action_id",new Text(action.actionId()),"operation",new Text(action.operation().value()),"body_sha256",new Text(action.bodySha256()),"phase",new Text(action.phase().name()),"original_receipt",ref(action.originalReceipt()));}
    private static Obj ref(ExactRef value){return object(parse(StrictJson.canonical(value.toJson())),"exact source ref");}
    private static ExactRef ref(Value value){return ExactRef.fromJson(toNode(value));}
    private static Value capability(Optional<String> value){return value.<Value>map(Text::new).orElse(Nil.INSTANCE);}
    private static Optional<String> capability(Value value){return value==Nil.INSTANCE?Optional.empty():Optional.of(text(value,"actual capability"));}
    private static Obj exact(Value value,Set<String> fields){Obj row=object(value,"funding source object");require(row.members().keySet().equals(fields),"exact funding source fields required");return row;}
    public static Obj evidenceJson(SourceEvidence value) {
        Objects.requireNonNull(value);var bodies=new ArrayList<Value>();for(var body:value.bodies())bodies.add(obj("domain",new Text(body.domain().name()),"original",ref(body.original()),"decoder_source",ref(body.decoderSource()),"pending",new Text(body.pending().name())));
        var installed=new ArrayList<Value>();for(var step:value.installed())installed.add(obj("operation",new Text(step.operation().value()),"kind",new Text(step.kind().name()),"guard_mode",new Text(step.guardMode().name()),"required_capability",capability(step.requiredCapability()),"implementation_source",ref(step.implementationSource()),"decoder_source",ref(step.decoderSource())));
        var families=new ArrayList<Value>();for(var family:value.families())families.add(obj("id",new Text(family.id()),"guard_mode",new Text(family.guardMode().name()),"required_capability",capability(family.requiredCapability()),"implementation_source",ref(family.implementationSource()),"decoder_source",ref(family.decoderSource()),"verifier_source",ref(family.verifierSource())));
        var actions=new ArrayList<Value>();for(var action:value.unresolvedActions())actions.add(actionJson(action));
        return obj("schema",new Text(SCHEMA),"scope",new Text(value.scope().name()),"native_funding_coverage",new Text(value.nativeFundingCoverage().name()),"unreceived_funding_credited_raw",new IntegerValue(java.math.BigInteger.ZERO),
                "current",object(parse(StrictJson.canonical(ProposalLifecycleCodec.observation(value.current()))),"current observation"),"source",object(parse(StrictJson.canonical(ProposalLifecycleCodec.source(value.source()))),"current G2 source"),"session_id",new Text(value.sessionId()),
                "canonical_head",ref(value.canonicalHead()),"ledger_sequence",new IntegerValue(java.math.BigInteger.valueOf(value.ledgerSequence())),"head_sha256",new Text(value.headSha256()),
                "bodies",new Arr(bodies),"installed",new Arr(installed),"families",new Arr(families),"canonical_action_count",new IntegerValue(java.math.BigInteger.valueOf(value.canonicalActionCount())),
                "canonical_action_inventory_sha256",new Text(value.canonicalActionInventorySha256()),"unresolved_actions",new Arr(actions));
    }
    public static byte[] encodeEvidence(SourceEvidence evidence){byte[] raw=encode(evidenceJson(evidence));require(raw.length<=StrictJson.EXPLICIT_MAX_BYTES,"funding source evidence exceeds bounded command domain");return raw;}
    public static SourceEvidence decodeEvidence(byte[] raw) {
        require(raw.length<=StrictJson.EXPLICIT_MAX_BYTES,"funding source evidence too large");
        Obj row=exact(parse(raw),Set.of("schema","scope","native_funding_coverage","unreceived_funding_credited_raw","current","source","session_id","canonical_head","ledger_sequence","head_sha256","bodies","installed","families","canonical_action_count","canonical_action_inventory_sha256","unresolved_actions"));
        require(new Text(SCHEMA).equals(row.get("schema"))&&new Text(Scope.OWNED_SUBMISSION_INVENTORY.name()).equals(row.get("scope"))
                &&new Text(NativeFundingCoverage.COMPLETE_DEBT_LOAN_REFUND_UNQUALIFIED.name()).equals(row.get("native_funding_coverage"))
                &&new IntegerValue(java.math.BigInteger.ZERO).equals(row.get("unreceived_funding_credited_raw")),"funding evidence scope/credit cannot acquire native financing qualification");
        var bodies=new ArrayList<BodyFact>();for(var value:array(row.get("bodies"),"body facts")){var b=exact(value,Set.of("domain","original","decoder_source","pending"));bodies.add(new BodyFact(FinanceStatePort.Domain.valueOf(text(b.get("domain"),"domain")),ref(b.get("original")),ref(b.get("decoder_source")),FinanceStatePort.Pending.valueOf(text(b.get("pending"),"pending"))));}
        var installed=new ArrayList<ExecutableStepBindings.InstalledStep>();for(var value:array(row.get("installed"),"installed facts")){var s=exact(value,Set.of("operation","kind","guard_mode","required_capability","implementation_source","decoder_source"));installed.add(new ExecutableStepBindings.InstalledStep(new OperationKey(text(s.get("operation"),"operation")),ExecutableStepBindings.Kind.valueOf(text(s.get("kind"),"kind")),ReadContract.GuardMode.valueOf(text(s.get("guard_mode"),"guard mode")),capability(s.get("required_capability")),ref(s.get("implementation_source")),ref(s.get("decoder_source"))));}
        var families=new ArrayList<FamilyFact>();for(var value:array(row.get("families"),"family facts")){var f=exact(value,Set.of("id","guard_mode","required_capability","implementation_source","decoder_source","verifier_source"));families.add(new FamilyFact(text(f.get("id"),"family ID"),ReadContract.GuardMode.valueOf(text(f.get("guard_mode"),"guard mode")),capability(f.get("required_capability")),ref(f.get("implementation_source")),ref(f.get("decoder_source")),ref(f.get("verifier_source"))));}
        var actions=new ArrayList<ActionFact>();for(var value:array(row.get("unresolved_actions"),"unresolved action facts")){var a=exact(value,Set.of("action_id","operation","body_sha256","phase","original_receipt"));actions.add(new ActionFact(text(a.get("action_id"),"action ID"),new OperationKey(text(a.get("operation"),"operation")),text(a.get("body_sha256"),"body SHA"),Phase.valueOf(text(a.get("phase"),"phase")),ref(a.get("original_receipt"))));}
        return new SourceEvidence(ProposalLifecycleCodec.decodeObservation(toNode(row.get("current"))),G2Wire.source(toNode(row.get("source"))),text(row.get("session_id"),"session ID"),ref(row.get("canonical_head")),integer(row.get("ledger_sequence"),"ledger sequence").longValueExact(),text(row.get("head_sha256"),"head SHA"),bodies,installed,families,
                integer(row.get("canonical_action_count"),"canonical action count").longValueExact(),text(row.get("canonical_action_inventory_sha256"),"canonical action inventory SHA"),actions);
    }
}
