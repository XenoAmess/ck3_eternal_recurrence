package org.xar.ck3.control.application.history;

import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJson;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.finance.GiftColdReadService;
import org.xar.ck3.control.application.planning.military.ForecastReadObservation;
import org.xar.ck3.control.application.planning.military.MilitaryReadObservation;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyBattleReadValue;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarReadCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.BattleResponses;
import org.xar.ck3.control.nativebridge.capabilities.army.ContactScopeObservation;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Original typed public read results. No canonical mutation, world effect or action/replay permission is granted. */
public final class DriverReadHistoryRowProducer {
    public static final String SOURCE_SCHEMA="xar.driver-read-history-source/v1";
    public static final String SOURCE_FIELD="read_history_source";
    public static final String RICH_SOURCE_SCHEMA="xar.driver-rich-read-history-source/v1";
    public static String sourceSchema(Kind kind){return Objects.requireNonNull(kind).isRich()?RICH_SOURCE_SCHEMA:SOURCE_SCHEMA;}
    private DriverReadHistoryRowProducer(){ }
    public enum Kind {
        COMBAT_V2("combat_simulation_inputs","game.command.query-combat-simulation-inputs-v2-N"),
        COMBAT_V3("combat_simulation_inputs","game.command.query-combat-simulation-inputs-v3-N"),
        WAR_ENTRY("war_entry_assessments","game.command.query-war-entry-assessments-v1-N"),
        CURRENT_KNIGHT("current_battle_knight","game.command.query-current-battle-knight-v1-N-N-N"),
        PHASE_TRACE("combat_phase_event_trace","game.command.query-combat-phase-event-trace-v1-N"),
        ROUTE_PREVIEW("route_preview","game.command.preview-move-army-N-to-N"),
        CONTACT_HORIZON("route_contact_horizon","game.command.query-route-contact-horizon-v1-N"),
        BATTLE_CONTROL("battle_control_snapshot","game.command.query-battle-control-snapshot-v1-N"),
        BATTLE_TRANSITION("battle_transition_snapshot","game.command.query-battle-transition-v1-N"),
        BATTLE_TERMINAL("battle_terminal_transition","game.command.query-battle-terminal-transition-v1-N"),
        REINFORCEMENT("battle_reinforcement_assignment","game.command.query-battle-reinforcement-assignment-v1-N"),
        DECLARABLE_WARS("declarable_wars","game.command.query-declarable-wars"),
        TERMINATION_OPTIONS("war_termination_options","game.command.query-war-termination-options-N"),
        TERMINATION_TERMS("war_termination_terms","game.command.query-war-termination-terms-v1-N"),
        CAMPAIGN_ROOT_CONTEXT("campaign_root_context","game.command.query-campaign-root-context-v1"),
        PROJECTED_CONTACT_SCOPE("projected_contact_scope",ContactScopeObservation.PROJECTED),
        ACTUAL_CONTACT_SCOPE("actual_contact_scope",ContactScopeObservation.ACTUAL),
        ARMY_STRENGTHS("army_strengths","game.command.query-army-strengths-v1"),
        ARMY_OBSERVER_SAMPLING("army_observer_research_sampling_v1","game.command.query-army-strengths-v1"),
        GIFT_COLD_RECOVERY("native",null);
        private final String payloadField,capability;
        Kind(String payloadField,String capability){this.payloadField=payloadField;this.capability=capability;}
        public String payloadField(){return payloadField;}
        public String capability(){return Objects.requireNonNull(capability,"source-qualified private history has no advertised capability");}
        public boolean hasQuerySequence(){return this!=ROUTE_PREVIEW&&this!=GIFT_COLD_RECOVERY&&this!=ARMY_OBSERVER_SAMPLING;}
        public boolean isRich(){return this==ARMY_STRENGTHS||this==ARMY_OBSERVER_SAMPLING;}
        public Optional<String> advertisedCapability(){return Optional.ofNullable(capability);}
        public boolean requiresExplicitEpisodeConnection(){return this==ROUTE_PREVIEW||this==CONTACT_HORIZON||this==TERMINATION_OPTIONS||this==CAMPAIGN_ROOT_CONTEXT||this==PROJECTED_CONTACT_SCOPE||this==ACTUAL_CONTACT_SCOPE||isRich();}
        public boolean hasQueriedFrame(){return this!=DECLARABLE_WARS&&this!=GIFT_COLD_RECOVERY;}
    }
    public record Input(RootReadContractCatalog catalog,ReadContract<?> contract,PlanningReadResult.Known<?> actual,long nextHistoryIndex) {
        public Input {Objects.requireNonNull(catalog);Objects.requireNonNull(contract);Objects.requireNonNull(actual);StrictJson.safe(nextHistoryIndex,1);}
    }
    /** Original caller policy only. This predicate supplies no source, frame, writer or adoption qualification. */
    public static boolean shouldRecord(PlanningReadResult.Known<?> actual) {
        Objects.requireNonNull(actual);
        if(actual.value() instanceof GiftColdReadService.Observation)return true;
        if(actual.value() instanceof ContactScopeObservation)return true;
        if(actual.value() instanceof FinanceReadContracts.Packet packet) {
            if(!packet.receipt().request().operation().equals(FinanceReadContracts.Query.ROOT.operation()))return false;
            StrictJson.require(packet.receipt().equals(actual.receipt())&&packet.receipt().contractId().equals(FinanceReadContracts.ROOT_CONTRACT_ID),
                    "campaign root history requires its actual sole Finance ROOT receipt");
            return FinanceReadContracts.rootCapture(packet.receipt().request().arguments())==FinanceReadContracts.RootCapture.PUBLIC_QUERY;
        }
        if(actual.value() instanceof ArmyWarReadCodec.Observation observed)return observed instanceof ArmyWarReadCodec.Declarations
                ||observed instanceof ArmyWarReadCodec.Options||observed instanceof ArmyWarReadCodec.Terms;
        if(actual.value() instanceof ArmyBattleReadValue||actual.value() instanceof BattleResponses.Reinforcement) {
            Obj arguments=actual.receipt().request().arguments();
            StrictJson.require(arguments.members().keySet().equals(Set.of("capture_context","public_arguments"))
                    &&arguments.get("public_arguments") instanceof Obj,"explicit original battle read capture context required");
            String capture=OpportunityJson.text(arguments.get("capture_context"),"battle capture context");
            String internal=actual.value() instanceof BattleResponses.Reinforcement?"INTERNAL_OBSERVATION":"INTERNAL_RETREAT";
            StrictJson.require(capture.equals("PUBLIC_QUERY")||capture.equals(internal),"unknown original typed battle read capture context");
            return capture.equals("PUBLIC_QUERY");
        }
        return actual.value() instanceof MilitaryReadObservation||actual.value() instanceof ForecastReadObservation;
    }
    public record ReadProvenance(Kind kind,String contractId,String requestId,ExactRef originalReceipt,
            ExactRef definitionSource,ExactRef decoderSource,ObservationIdentity sourceFrame,G2Source source,String sessionId,
            BigInteger connectionGeneration,Optional<BigInteger> querySequence,Obj arguments,List<ExactRef> supportingEvidence,List<ExactRef> componentReceipts,Optional<DriverReadHistoryRichMaterial.PublicNumbers> publicNumbers) {
        public ReadProvenance(Kind kind,String contractId,String requestId,ExactRef originalReceipt,
                ExactRef definitionSource,ExactRef decoderSource,ObservationIdentity sourceFrame,G2Source source,String sessionId,
                BigInteger connectionGeneration,Optional<BigInteger> querySequence,Obj arguments,List<ExactRef> supportingEvidence) {
            this(kind,contractId,requestId,originalReceipt,definitionSource,decoderSource,sourceFrame,source,sessionId,connectionGeneration,
                    querySequence,arguments,supportingEvidence,List.of(),Optional.empty());
        }
        public ReadProvenance {
            Objects.requireNonNull(kind);StrictJson.text(contractId);StrictJson.text(requestId);Objects.requireNonNull(originalReceipt);
            Objects.requireNonNull(definitionSource);Objects.requireNonNull(decoderSource);Objects.requireNonNull(sourceFrame);Objects.requireNonNull(source);
            StrictJson.text(sessionId);unsigned(connectionGeneration,true,"actual connection generation");querySequence=Objects.requireNonNull(querySequence);
            querySequence.ifPresent(value->unsigned(value,true,"actual query sequence"));Objects.requireNonNull(arguments);supportingEvidence=List.copyOf(supportingEvidence);componentReceipts=List.copyOf(componentReceipts);publicNumbers=Objects.requireNonNull(publicNumbers);
            StrictJson.require(publicNumbers.isPresent()==kind.isRich(),"rich source requires its fixed original public number roles");
            StrictJson.require(kind.isRich()?componentReceipts.size()>=1&&componentReceipts.size()<=(kind==Kind.ARMY_STRENGTHS?2:1)
                    &&componentReceipts.contains(originalReceipt)&&new java.util.HashSet<>(componentReceipts).size()==componentReceipts.size()
                    :componentReceipts.isEmpty(),"finite original rich component receipts required");
            StrictJson.require(originalReceipt.bytes()>0&&definitionSource.bytes()>0&&decoderSource.bytes()>0&&source.machineId().equals(sourceFrame.machineId())
                    &&querySequence.isPresent()==kind.hasQuerySequence()&&supportingEvidence.size()<=260
                    &&new java.util.HashSet<>(supportingEvidence).size()==supportingEvidence.size(),"complete typed original read source required");
        }
    }
    public record RawHistoryRow(long index,String command,boolean ok,Obj result,ReadProvenance provenance) {
        public RawHistoryRow {
            StrictJson.safe(index,1);StrictJson.text(command);Objects.requireNonNull(result);Objects.requireNonNull(provenance);
            StrictJson.require(ok&&new Text(command).equals(result.get("step")),"only a source-decoded successful read row is accepted here");
            requireResult(provenance,result);
        }
        public Obj toJson(){return new Obj(java.util.Map.of("index",integer(index),"command",new Text(command),"ok",new Bool(ok),"result",result,SOURCE_FIELD,sourceJson(provenance)));}
        public byte[] encode(){return OpportunityJson.encode(ordered(toJson()));}
        public DriverStateSnapshot.HistoryEntry historyEntry(){return new DriverStateSnapshot.HistoryEntry(index,new DriverStateSnapshot.Value(encode()));}
    }
    /** Only the original receipt replay path can mint this value. Artifact retention is not canonical history publication. */
    public static final class Candidate {
        private final RawHistoryRow row;private final ExactRef rowReference;private final Optional<ExactRef> fullResultReference;
        private Candidate(RawHistoryRow row,ExactRef rowReference){this(row,rowReference,Optional.empty());}
        private Candidate(RawHistoryRow row,ExactRef rowReference,Optional<ExactRef> fullResultReference){this.row=row;this.rowReference=rowReference;this.fullResultReference=fullResultReference;}
        public Optional<ExactRef> fullResultReference(){return fullResultReference;}
        public RawHistoryRow row(){return row;}
        public DriverStateSnapshot.HistoryEntry historyEntry(){return row.historyEntry();}
        public ExactRef rowReference(){return rowReference;}
        public ExactRef readReference(){return row.provenance().originalReceipt();}
        public ExactRef definitionSource(){return row.provenance().definitionSource();}
        public ExactRef decoderSource(){return row.provenance().decoderSource();}
        public ReadProvenance provenance(){return row.provenance();}
    }
    public static Candidate prepare(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,ReadContract<?> contract,
            PlanningReadResult.Known<?> actual,long nextHistoryIndex) {
        Objects.requireNonNull(bound);RawHistoryRow row=derive(bound,new Input(catalog,contract,actual,nextHistoryIndex));
        ExactRef reference=bound.preserveMaterial(new RawJson(row.encode()));
        StrictJson.require(reference.equals(bound.materialReferenceOf(new RawJson(row.encode())))&&decode(bound.loadMaterial(reference).bytes()).equals(row),
                "original complete read row archive/serialization changed");return new Candidate(row,reference);
    }
    /** Final source-owned rich projection only; components retain both real A/B receipts without publishing an intermediate row. */
    public static Candidate prepareRich(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,ReadContract<?> contract,
            PlanningReadResult.Known<?> actual,List<? extends PlanningReadResult.Known<?>> components,long nextHistoryIndex) {
        List<ExactRef> refs=components.stream().map(value -> {
            StrictJson.require(bound.loadRead(value.originalReceipt()).equals(value.receipt()),"rich component differs from actual archived receipt");
            return value.originalReceipt();
        }).toList();
        RawHistoryRow row=derive(bound,new Input(catalog,contract,actual,nextHistoryIndex),refs,ArtifactMode.PRESERVE_COMPLETE);
        RawJson complete=new RawJson(OpportunityJson.encode(ordered(row.result())));
        ExactRef completeReference=bound.materialReferenceOf(complete);
        requireRichArtifact(bound,row);
        StrictJson.require(completeReference.equals(bound.materialReferenceOf(complete)),"original rich full-result reference changed");
        RawJson original=new RawJson(row.encode());ExactRef reference=bound.preserveMaterial(original);
        StrictJson.require(reference.equals(bound.materialReferenceOf(original))&&decode(bound.loadMaterial(reference).bytes()).equals(row),
                "complete rich read row archive/serialization changed");
        return new Candidate(row,reference,Optional.of(completeReference));
    }
    /** Original artifacts plus the identical installed pure decoder only; this method never preserves or publishes anything. */
    public static Candidate replay(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,ReadContract<?> contract,
            PlanningReadResult.Known<?> actual,Candidate original) {
        Objects.requireNonNull(original);RawHistoryRow row=derive(bound,new Input(catalog,contract,actual,original.row().index()),original.row().provenance().componentReceipts());
        requireRichArtifact(bound,row);
        StrictJson.require(original.fullResultReference().equals(row.provenance().kind().isRich()?Optional.of(fullReference(bound,row)):Optional.empty()),"retained rich full-result custody changed");
        StrictJson.require(row.equals(original.row())&&decode(bound.loadMaterial(original.rowReference()).bytes()).equals(row)
                &&bound.materialReferenceOf(new RawJson(row.encode())).equals(original.rowReference()),"actual retained read row/source replay changed");return original;
    }
    /** Reuses only an original canonical row's actual receipt and installed pure decoder; no new artifact, request or freshness is minted. */
    public static <T> PlanningReadResult.Known<T> replayCanonical(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,
            ReadContract<T> identicalInstalled,RawHistoryRow original) {
        Objects.requireNonNull(bound);Objects.requireNonNull(catalog);Objects.requireNonNull(identicalInstalled);Objects.requireNonNull(original);
        StrictJson.require(catalog.containsIdentity(identicalInstalled),"canonical replay requires the identical installed read contract");
        ExactRef reference=original.provenance().originalReceipt();PlanningReadReceipt receipt=bound.loadRead(reference);
        T value=identicalInstalled.replay(receipt);var known=new PlanningReadResult.Known<>(value,receipt,reference);
        RawHistoryRow replayed=derive(bound,new Input(catalog,identicalInstalled,known,original.index()),original.provenance().componentReceipts());
        requireRichArtifact(bound,replayed);
        StrictJson.require(replayed.equals(original),"canonical read row/source differs from complete original pure replay");
        return known;
    }
    private static RawHistoryRow derive(ActionPorts.OutcomeArchive bound,Input input) {
        return derive(bound,input,List.of());
    }
    private enum ArtifactMode { REQUIRE_RETAINED, PRESERVE_COMPLETE }
    private static RawHistoryRow derive(ActionPorts.OutcomeArchive bound,Input input,List<ExactRef> richComponents) {
        return derive(bound,input,richComponents,ArtifactMode.REQUIRE_RETAINED);
    }
    private static RawHistoryRow derive(ActionPorts.OutcomeArchive bound,Input input,List<ExactRef> richComponents,ArtifactMode artifactMode) {
        var catalog=input.catalog();var contract=input.contract();var known=input.actual();
        boolean rich=!richComponents.isEmpty();
        StrictJson.require(rich?contract.originalHistoryKind().isPresent():shouldRecord(known),
                "read has no explicit installed original history policy");
        StrictJson.require(catalog.containsIdentity(contract)&&contract.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                &&contract.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP,
                "actual identical installed public gameplay read contract required");
        var installed=catalog.installed().stream().filter(value->value.contract()==contract).toList();
        StrictJson.require(installed.size()==1,"one original read definition/decoder binding required");
        PlanningReadReceipt receipt=bound.loadRead(known.originalReceipt());
        StrictJson.require(receipt.equals(known.receipt())&&bound.readReferenceOf(receipt).equals(known.originalReceipt())
                &&receipt.contractId().equals(contract.contractId())&&receipt.request().operation().equals(contract.operation()),"actual original archived read/contract differs");
        StrictJson.require(receipt.request().origin() instanceof CommandOrigin.Gameplay,"private/frontend/terminal read cannot become ordinary gameplay history");
        for(var guard:List.of(receipt.before(),receipt.after()))
            StrictJson.require(guard.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP&&guard.paused()&&guard.mapReady()&&guard.playerAlive()
                    &&guard.binding().origin().equals(receipt.request().origin()),"actual read crossed its living paused source frame");
        StrictJson.require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),"actual read crossed its complete semantic/modal binding");
        // Unlike decode(), this explicit source-installed route must not update a live forecast/cache slot.
        Obj nativeResult=nativeResult(receipt);
        Object replayed=contract.replay(receipt);
        DriverReadHistoryRichMaterial.Projection projection=rich?contract.projectOriginalHistory(receipt):null;
        Kind kind=rich?richKind(projection.kind()):kind(replayed),claimedKind=rich?kind:kind(known.value());
        Obj result=rich?DriverJson.object(projection.fullResult().bytes(),RawJson.MAXIMUM_BYTES):normalized(replayed,receipt,nativeResult);
        Obj claimed=rich?result:normalized(known.value(),receipt,nativeResult);
        boolean completeValueEqual=rich?true:replayed instanceof FinanceReadContracts.Packet left&&known.value() instanceof FinanceReadContracts.Packet right
                ?left.receipt().equals(right.receipt())&&left.result().equals(right.result())&&left.originalResult().equals(right.originalResult())
                :replayed instanceof ArmyBattleReadValue left&&known.value() instanceof ArmyBattleReadValue right
                ?left.kind()==right.kind()&&left.sequence().equals(right.sequence())&&left.normalized().equals(right.normalized())&&left.extensions().equals(right.extensions())
                :replayed instanceof GiftColdReadService.Observation left&&known.value() instanceof GiftColdReadService.Observation right
                ?left.receipt().equals(right.receipt())&&left.originalResult().equals(right.originalResult())&&left.originalPost().equals(right.originalPost())
                :replayed.equals(known.value());
        StrictJson.require(kind==claimedKind&&result.equals(claimed)&&completeValueEqual&&contract.requiredCapability().equals(kind.advertisedCapability())
                &&contract.permissionMode()==(kind==Kind.GIFT_COLD_RECOVERY?ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE:ReadContract.PermissionMode.ADVERTISED_CAPABILITY),
                "claimed typed read differs from the original pure decoder/kind/permission");
        Optional<BigInteger> querySequence=optionalSequence(nativeResult,kind);
        StrictJson.require(querySequence.equals(optionalSequence(result,kind)),"normalized read replaced its actual native query sequence");
        if(nativeResult.members().containsKey("snapshot_revision"))
            StrictJson.require(OpportunityJson.integer(nativeResult.get("snapshot_revision"),"native snapshot revision").equals(receipt.request().before().frame().identity().nativeRevision()),
                    "actual query native snapshot revision differs from guarded source");
        var support=new java.util.LinkedHashSet<ExactRef>();
        for(var guard:List.of(receipt.before(),receipt.after())) {
            support.add(guard.binding().nativeEvidence());support.add(guard.binding().capabilityEvidence());support.addAll(guard.binding().supportingEvidence());
        }
        if(rich) {
            support.addAll(projection.sourceClosure());
            requireRichComponents(bound,catalog,contract,receipt,richComponents,support);
        }
        var provenance=new ReadProvenance(kind,receipt.contractId(),receipt.requestId(),known.originalReceipt(),contract.sourceRef(),installed.getFirst().decoderSource(),
                receipt.request().before(),receipt.request().source(),receipt.request().sessionId(),receipt.before().binding().connectionGeneration(),querySequence,
                receipt.request().arguments(),List.copyOf(support),richComponents,rich?Optional.of(projection.publicNumbers()):Optional.empty());
        RawHistoryRow validated=new RawHistoryRow(input.nextHistoryIndex(),receipt.request().operation().value(),true,result,provenance);
        return rich?completeRichArtifact(bound,validated,artifactMode):validated;
    }
    /** All original source/frame/component/value validation precedes the first archival write. Replay only reads retained material. */
    private static RawHistoryRow completeRichArtifact(ActionPorts.OutcomeArchive bound,RawHistoryRow validated,ArtifactMode mode) {
        StrictJson.require(validated.provenance().supportingEvidence().size()<260,"rich source closure must reserve its complete-result artifact slot");
        RawJson complete=new RawJson(OpportunityJson.encode(ordered(validated.result())));
        ExactRef original=mode==ArtifactMode.PRESERVE_COMPLETE?bound.preserveMaterial(complete):bound.materialReferenceOf(complete);
        StrictJson.require(bound.materialReferenceOf(complete).equals(original)
                &&DriverJson.object(bound.loadMaterial(original).bytes(),RawJson.MAXIMUM_BYTES).equals(validated.result()),
                "original rich full-result retention/lookup changed");
        ReadProvenance source=validated.provenance();var support=new java.util.LinkedHashSet<>(source.supportingEvidence());support.add(original);
        var retained=new ReadProvenance(source.kind(),source.contractId(),source.requestId(),source.originalReceipt(),source.definitionSource(),
                source.decoderSource(),source.sourceFrame(),source.source(),source.sessionId(),source.connectionGeneration(),source.querySequence(),
                source.arguments(),List.copyOf(support),source.componentReceipts(),source.publicNumbers());
        return new RawHistoryRow(validated.index(),validated.command(),validated.ok(),validated.result(),retained);
    }
    private static Kind richKind(DriverReadHistoryRichMaterial.Kind kind) {
        return switch(kind) {case ARMY_STRENGTHS->Kind.ARMY_STRENGTHS;case ARMY_OBSERVER_SAMPLING->Kind.ARMY_OBSERVER_SAMPLING;case PUBLIC_EXECUTE_QUERY->throw new IllegalArgumentException("encoded execute queries require their finite dedicated original-command producer");};
    }
    private static ExactRef fullReference(ActionPorts.OutcomeArchive bound,RawHistoryRow row) {
        return bound.materialReferenceOf(new RawJson(OpportunityJson.encode(ordered(row.result()))));
    }
    private static void requireRichArtifact(ActionPorts.OutcomeArchive bound,RawHistoryRow row) {
        if(!row.provenance().kind().isRich())return;
        ExactRef original=fullReference(bound,row);
        StrictJson.require(row.provenance().supportingEvidence().contains(original)
                &&DriverJson.object(bound.loadMaterial(original).bytes(),RawJson.MAXIMUM_BYTES).equals(row.result()),
                "rich history lost its original complete numeric Driver result artifact");
    }
    private static void requireRichComponents(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,ReadContract<?> finalContract,
            PlanningReadReceipt originalFinal,List<ExactRef> components,java.util.LinkedHashSet<ExactRef> support) {
        StrictJson.require(components.size()>=1&&components.size()<=(finalContract.originalHistoryKind().orElseThrow()==DriverReadHistoryRichMaterial.Kind.ARMY_STRENGTHS?2:1)&&components.contains(bound.readReferenceOf(originalFinal))
                &&new java.util.HashSet<>(components).size()==components.size(),"one final receipt and at most one actual comparison component required");
        for(ExactRef reference:components) {
            PlanningReadReceipt receipt=bound.loadRead(reference);
            StrictJson.require(bound.readReferenceOf(receipt).equals(reference)&&receipt.request().before().equals(originalFinal.request().before())
                    &&receipt.request().source().equals(originalFinal.request().source())&&receipt.request().sessionId().equals(originalFinal.request().sessionId())
                    &&receipt.before().binding().connectionGeneration().equals(originalFinal.before().binding().connectionGeneration())
                    &&receipt.request().operation().equals(originalFinal.request().operation()),"rich component crossed its real original query/frame/source/session");
            ReadContract<?> component=receipt.contractId().equals(finalContract.contractId())?finalContract:
                    finalContract.originalContract(receipt.contractId()).orElseThrow(()->new IllegalArgumentException("actual rich component contract unavailable"));
            StrictJson.require(catalog.containsIdentity(component)&&component.originalHistoryKind().equals(finalContract.originalHistoryKind()),
                    "rich component requires its identical source-installed pure decoder");
            var installed=catalog.installed().stream().filter(value->value.contract()==component).toList();
            StrictJson.require(installed.size()==1,"one original rich component decoder binding required");
            nativeResult(receipt);component.replay(receipt);
            support.add(reference);support.add(component.sourceRef());support.add(installed.getFirst().decoderSource());
            support.addAll(component.projectOriginalHistory(receipt).sourceClosure());
        }
    }
    private static Obj nativeResult(PlanningReadReceipt receipt) {
        var ack=receipt.original();byte[] packet=ack.originalPacket(),frame=ack.originalFrame().bytes();
        StrictJson.require(packet.length>=5&&ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt()==frame.length
                &&packet.length==frame.length+4&&Arrays.equals(Arrays.copyOfRange(packet,4,packet.length),frame),"actual original native read LE frame differs");
        Obj envelope=DriverJson.object(frame,DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require(new Text("command_result").equals(envelope.get("type"))&&integer(1).equals(envelope.get("protocol_version"))
                &&new Text(receipt.requestId()).equals(envelope.get("request_id"))&&new Bool(true).equals(envelope.get("ok"))&&ack.nativeOk(),
                "actual read ACK envelope identity/status differs");
        Obj result=OpportunityJson.object(envelope.get("result"),"actual native read result");
        StrictJson.require(ack.originalResultToken().isPresent()&&DriverJson.object(ack.originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES).equals(result)
                &&new Text(receipt.request().operation().value()).equals(result.get("step"))&&new Bool(true).equals(result.get("accepted")),
                "actual complete native query token/step/accepted differs");return result;
    }
    private static Kind kind(Object actual) {
        if(actual instanceof GiftColdReadService.Observation)return Kind.GIFT_COLD_RECOVERY;
        if(actual instanceof ContactScopeObservation observed)return observed.query() instanceof ContactScopeObservation.Projected?Kind.PROJECTED_CONTACT_SCOPE:Kind.ACTUAL_CONTACT_SCOPE;
        if(actual instanceof FinanceReadContracts.Packet packet) {
            StrictJson.require(packet.receipt().request().operation().equals(FinanceReadContracts.Query.ROOT.operation())
                    &&packet.receipt().contractId().equals(FinanceReadContracts.ROOT_CONTRACT_ID),"only the original ROOT Finance packet has public history policy");return Kind.CAMPAIGN_ROOT_CONTEXT;
        }
        if(actual instanceof ArmyWarReadCodec.Observation observed)return switch(observed.method()) {
            case QUERY_DECLARABLE_WARS->Kind.DECLARABLE_WARS;case QUERY_WAR_TERMINATION_OPTIONS->Kind.TERMINATION_OPTIONS;case QUERY_WAR_TERMINATION_TERMS->Kind.TERMINATION_TERMS;
            default->throw new IllegalArgumentException("this original Army war read has no public history policy here");
        };
        if(actual instanceof BattleResponses.Reinforcement)return Kind.REINFORCEMENT;
        if(actual instanceof ArmyBattleReadValue observed)return switch(observed.kind()){case CONTROL->Kind.BATTLE_CONTROL;case TRANSITION->Kind.BATTLE_TRANSITION;case TERMINAL->Kind.BATTLE_TERMINAL;};
        if(actual instanceof MilitaryReadObservation observed)return switch(observed.kind()) {case ROUTE_PREVIEW->Kind.ROUTE_PREVIEW;case CONTACT_HORIZON->Kind.CONTACT_HORIZON;};
        if(actual instanceof ForecastReadObservation observed)return switch(observed.kind()) {
            case COMBAT_V2->Kind.COMBAT_V2;case COMBAT_V3->Kind.COMBAT_V3;case WAR_ENTRY->Kind.WAR_ENTRY;case CURRENT_KNIGHT->Kind.CURRENT_KNIGHT;case PHASE_TRACE->Kind.PHASE_TRACE;
        };
        throw new IllegalArgumentException("read has no original public execute_step history policy among the twenty finite typed read kinds");
    }
    private static Obj normalized(Object actual,PlanningReadReceipt receipt,Obj nativeResult) {
        if(actual instanceof GiftColdReadService.Observation observed) {
            StrictJson.require(observed.receipt().equals(receipt)&&observed.originalResult().equals(nativeResult),"Gift cold typed observation changed its actual original receipt/token");
            return observed.originalResult();
        }
        if(actual instanceof ContactScopeObservation observed)return contactResult(observed,receipt,nativeResult);
        if(actual instanceof FinanceReadContracts.Packet packet)return rootResult(packet,receipt,nativeResult);
        if(actual instanceof ArmyWarReadCodec.Observation observed)return observed.normalizedResult();
        if(actual instanceof BattleResponses.Reinforcement observed)return reinforcementResult(observed,receipt,nativeResult);
        if(actual instanceof ArmyBattleReadValue observed)return battleResult(observed,receipt,nativeResult);
        if(actual instanceof MilitaryReadObservation observed)return observed.normalizedResult();
        if(actual instanceof ForecastReadObservation observed)return observed.normalizedResult();
        throw new IllegalArgumentException("unsupported typed read history value");
    }
    /** Shared Contact owner owns every field/domain decoder; history adds only original receipt/native binding. */
    private static Obj contactResult(ContactScopeObservation actual,PlanningReadReceipt receipt,Obj nativeResult) {
        StrictJson.require(receipt.request().arguments().members().isEmpty()
                &&receipt.request().operation().value().equals(actual.query().step()),"Contact history changed its actual operation/empty public arguments");
        Obj normalized=actual.normalizedResult();var original=new LinkedHashMap<>(normalized.members());
        for(String key:List.of("queried_snapshot_id","queried_revision","queried_native_revision","queried_connection_generation","queried_episode_run_id"))original.remove(key);
        StrictJson.require(new Obj(original).equals(nativeResult),"Contact typed scope differs from its complete original native token");
        return normalized;
    }
    /** The row retains the complete original ROOT token, including raw optional components; pure replay owns its normalized view. */
    private static Obj rootResult(FinanceReadContracts.Packet actual,PlanningReadReceipt receipt,Obj nativeResult) {
        StrictJson.require(actual.receipt().equals(receipt)&&actual.originalResult().equals(nativeResult),"campaign ROOT packet differs from the original receipt/native token");
        var frame=receipt.request().before().frame();
        Obj normalized=CampaignRootContextJson.normalizeNativeResult(nativeResult,frame.identity().dateRaw(),frame.identity().nativeRevision());
        StrictJson.require(actual.result().equals(normalized)
                &&FinanceReadContracts.rootCapture(receipt.request().arguments())==FinanceReadContracts.RootCapture.PUBLIC_QUERY,
                "original ROOT decoder value or explicit public capture differs");
        return nativeResult.with("queried_snapshot_id",new Text(frame.snapshotId())).with("queried_revision",new IntegerValue(frame.revision()))
                .with("queried_native_revision",new IntegerValue(frame.identity().nativeRevision()))
                .with("queried_connection_generation",new IntegerValue(receipt.before().binding().connectionGeneration()))
                .with("queried_episode_run_id",new Text(frame.episodeRunId()));
    }
    /** Strict reinforcement normalization is owned by ArmyReinforcementCodec; these are the original Driver's outer mirrors only. */
    private static Obj reinforcementResult(BattleResponses.Reinforcement actual,PlanningReadReceipt receipt,Obj nativeResult) {
        Obj normalized=actual.originalFrame();var frame=receipt.request().before().frame();
        StrictJson.require(actual.frame().nativeRevision().value().equals(frame.identity().nativeRevision())
                &&BigInteger.valueOf(actual.frame().dateRaw()).equals(frame.identity().dateRaw())
                &&actual.frame().querySequence() instanceof ArmyTypes.Present<ArmyTypes.UInt64> sequence
                &&new IntegerValue(sequence.value().value()).equals(nativeResult.get("query_sequence")),
                "typed reinforcement original frame/sequence differs from actual native source");
        StrictJson.require(new IntegerValue(BigInteger.valueOf(actual.selected().value())).equals(normalized.get("selected_public_cunit_id"))
                &&normalized.equals(OpportunityJson.object(nativeResult.get("battle_reinforcement_assignment"),"actual reinforcement original")),
                "typed reinforcement subject/normalized original differs from native assignment");
        var fields=new LinkedHashMap<>(nativeResult.members());fields.put("battle_reinforcement_assignment",normalized);fields.put("status",normalized.get("status"));
        for(String key:List.of("selected_public_cunit_id","selected_native_carmy_id","coordinator_id","unit_stack_stored_index","subunit_stored_index",
                "signal","assignment","route","native_order","contact_projection","battle_reinforcement_assignment_ready","unavailable_reason")) {
            StrictJson.require(normalized.members().containsKey(key),"original reinforcement compatible mirror missing: "+key);fields.put(key,normalized.get(key));
        }
        fields.put("queried_snapshot_id",new Text(frame.snapshotId()));fields.put("queried_revision",new IntegerValue(frame.revision()));
        fields.put("queried_native_revision",new IntegerValue(frame.identity().nativeRevision()));return new Obj(fields);
    }
    /** One compatible outer-history projection; the sole M5 decoder still owns every nested domain field. */
    private static Obj battleResult(ArmyBattleReadValue actual,PlanningReadReceipt receipt,Obj nativeResult) {
        Kind kind=kind(actual);Obj normalized=actual.normalized();var fields=new LinkedHashMap<>(nativeResult.members());
        StrictJson.text(OpportunityJson.text(normalized.get("status"),"actual normalized M5 status"));
        StrictJson.require(new IntegerValue(actual.sequence()).equals(nativeResult.get("query_sequence")),"M5 typed query sequence differs from actual Native outer");
        fields.put(kind.payloadField(),normalized);fields.put("status",normalized.get("status"));
        Set<String> extensionNames=switch(actual.kind()){case CONTROL->Set.of("active_combat_resume_inputs_v1");case TRANSITION->Set.of();case TERMINAL->Set.of("person_six_stage_captures","person_installed_transfers");};
        StrictJson.require(extensionNames.containsAll(actual.extensions().members().keySet()),"unknown typed M5 outer extension");
        for(String key:extensionNames)StrictJson.require(!nativeResult.members().containsKey(key)||actual.extensions().members().containsKey(key),"actual M5 outer extension has no complete typed decoder value");
        for(var extension:actual.extensions().members().entrySet()) {
            StrictJson.require(nativeResult.members().containsKey(extension.getKey()),"normalized M5 extension has no original outer source");fields.put(extension.getKey(),extension.getValue());
        }
        List<String> required=switch(actual.kind()) {
            case CONTROL->List.of("selected_public_cunit_id","selected_native_carmy_id","selected_owner_character_id","combat_province_id","side_index","side_scope","affected_public_cunit_ids_in_stored_order","unaffected_same_side_public_cunit_ids_in_stored_order","side_flags","legality");
            case TRANSITION->List.of("combat_id","province_id","phase","phase_raw","phase_day","winner_side","winner_raw","forced_winner_side","forced_winner_raw","finalized","battle_result_id","attacker_public_cunit_ids_in_stored_order","defender_public_cunit_ids_in_stored_order","battle_transition_ready");
            case TERMINAL->List.of("prior_combat_id","subject_public_cunit_id","terminal_journal","prior","removal","subject","successor","battle_terminal_transition_ready","unavailable_reason");
        };
        for(String key:required){StrictJson.require(normalized.members().containsKey(key),"original M5 compatible mirror missing: "+key);fields.put(key,normalized.get(key));}
        List<String> optional=switch(actual.kind()){case CONTROL->List.of();case TRANSITION->List.of("current_observation","actual_geography_v1");case TERMINAL->List.of("character_observations");};
        for(String key:optional)if(normalized.members().containsKey(key))fields.put(key,normalized.get(key));
        var frame=receipt.request().before().frame();fields.put("queried_snapshot_id",new Text(frame.snapshotId()));fields.put("queried_revision",new IntegerValue(frame.revision()));
        fields.put("queried_native_revision",new IntegerValue(frame.identity().nativeRevision()));return new Obj(fields);
    }
    private static Optional<BigInteger> optionalSequence(Obj result,Kind kind) {
        if(!result.members().containsKey("query_sequence")) {
            StrictJson.require(!kind.hasQuerySequence(),"actual native query sequence is required");return Optional.empty();
        }
        StrictJson.require(kind.hasQuerySequence(),"original route preview does not invent a query sequence");
        BigInteger sequence=OpportunityJson.integer(result.get("query_sequence"),"actual query sequence");unsigned(sequence,true,"actual query sequence");return Optional.of(sequence);
    }
    private static void requireResult(ReadProvenance source,Obj result) {
        var frame=source.sourceFrame().frame();
        StrictJson.text(OpportunityJson.text(result.get("status"),"actual normalized read status"));
        boolean payload=source.kind()==Kind.DECLARABLE_WARS||source.kind()==Kind.ARMY_STRENGTHS?result.get(source.kind().payloadField()) instanceof Arr:result.get(source.kind().payloadField()) instanceof Obj;
        StrictJson.require(new Bool(true).equals(result.get("accepted"))&&payload&&optionalSequence(result,source.kind()).equals(source.querySequence()),
                "normalized complete read payload/query sequence differs");
        if(source.kind().hasQueriedFrame())StrictJson.require(new Text(frame.snapshotId()).equals(result.get("queried_snapshot_id"))
                &&new IntegerValue(frame.revision()).equals(result.get("queried_revision"))
                &&new IntegerValue(frame.identity().nativeRevision()).equals(result.get("queried_native_revision")),
                "normalized complete read queried source differs");
        if(source.kind().isRich()) {
            new DriverReadHistoryRichMaterial.Projection(source.kind()==Kind.ARMY_STRENGTHS?DriverReadHistoryRichMaterial.Kind.ARMY_STRENGTHS:DriverReadHistoryRichMaterial.Kind.ARMY_OBSERVER_SAMPLING,
                    new RawJson(OpportunityJson.encode(result)),source.publicNumbers().orElseThrow(),List.of(source.definitionSource(),source.decoderSource()).stream().distinct().toList());
            StrictJson.require(new IntegerValue(frame.identity().dateRaw()).equals(result.get("queried_date_raw")),
                    "rich Driver history changed its original queried date");
            if(source.kind()==Kind.ARMY_OBSERVER_SAMPLING)StrictJson.require(new IntegerValue(frame.identity().player()).equals(result.get("queried_player_character_id"))
                    &&source.arguments().members().keySet().equals(Set.of("observer_family"))
                    &&source.arguments().get("observer_family").equals(result.get("observer_family")),"sampling history changed its original player/selected family");
        }
        if(source.kind()==Kind.GIFT_COLD_RECOVERY) {
            StrictJson.require(source.contractId().equals("ordinary-finance-gift-cold-read/v1")
                    &&new Text(GiftColdReadService.OPERATION.value()).equals(result.get("step")),"Gift cold history requires its one original contract/operation");
            GiftColdReadService.requireHistoryResult(result,source.arguments(),source.sourceFrame());
        }
        if(source.kind()==Kind.TERMINATION_TERMS)StrictJson.require(new IntegerValue(source.connectionGeneration()).equals(result.get("queried_connection_generation"))
                &&new Text(frame.episodeRunId()).equals(result.get("episode_run_id")),"original terms episode/connection binding missing or changed");
        if(source.kind().requiresExplicitEpisodeConnection())StrictJson.require(new IntegerValue(source.connectionGeneration()).equals(result.get("queried_connection_generation"))
                &&new Text(frame.episodeRunId()).equals(result.get("queried_episode_run_id")),"original public read episode/connection binding missing or changed");
        if(source.kind()==Kind.PROJECTED_CONTACT_SCOPE||source.kind()==Kind.ACTUAL_CONTACT_SCOPE) {
            StrictJson.require(source.arguments().members().isEmpty(),"Contact history requires exact empty public arguments");
            var decoded=ContactScopeObservation.decodeHistoryResult(result,frame.identity().dateRaw().intValueExact());
            StrictJson.require(kind(decoded)==source.kind()&&decoded.query().capability().equals(source.kind().capability()),
                    "Contact history operation/scope/kind differs from the sole shared decoder");
        }
        if(source.kind()==Kind.CAMPAIGN_ROOT_CONTEXT) {
            StrictJson.require(new Text(FinanceReadContracts.Query.ROOT.operation().value()).equals(result.get("step"))
                    &&source.contractId().equals(FinanceReadContracts.ROOT_CONTRACT_ID)
                    &&FinanceReadContracts.rootCapture(source.arguments())==FinanceReadContracts.RootCapture.PUBLIC_QUERY,"ROOT history operation/contract/public arguments differ");
            var original=new LinkedHashMap<>(result.members());for(String key:List.of("queried_snapshot_id","queried_revision","queried_native_revision","queried_connection_generation","queried_episode_run_id"))original.remove(key);
            CampaignRootContextJson.normalizeNativeResult(new Obj(original),frame.identity().dateRaw(),frame.identity().nativeRevision());
        }
    }
    private static Obj sourceJson(ReadProvenance source) {
        var node=StrictJson.object();node.put("schema",sourceSchema(source.kind()));node.put("kind",source.kind().name());node.put("payload_field",source.kind().payloadField());
        node.put("contract_id",source.contractId());node.put("request_id",source.requestId());node.set("original_receipt",source.originalReceipt().toJson());
        node.set("definition_source",source.definitionSource().toJson());node.set("decoder_source",source.decoderSource().toJson());
        node.set("source_frame",ProposalLifecycleCodec.observation(source.sourceFrame()));node.set("source",ProposalLifecycleCodec.source(source.source()));node.put("session_id",source.sessionId());
        node.put("connection_generation",source.connectionGeneration());source.querySequence().ifPresent(value->node.put("query_sequence",value));
        if(source.kind().isRich()) {var components=node.putArray("component_receipts");source.componentReceipts().forEach(ref->components.add(ref.toJson()));node.set("public_number_roles",OpportunityJson.toNode(source.publicNumbers().orElseThrow().toJson()));}
        node.set("arguments",OpportunityJson.toNode(source.arguments()));var support=node.putArray("supporting_evidence");source.supportingEvidence().forEach(ref->support.add(ref.toJson()));
        return DriverJson.object(StrictJson.canonical(node),DriverJson.MAX_NATIVE_BYTES);
    }
    public static RawHistoryRow decode(byte[] original) {
        Obj row=DriverJson.object(original,DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require(row.members().keySet().equals(Set.of("index","command","ok","result",SOURCE_FIELD)),"exact complete original read row required");
        Obj source=OpportunityJson.object(row.get(SOURCE_FIELD),"actual read history source");
        Kind kind=requireSourceHeader(source);
        var support=OpportunityJson.array(source.get("supporting_evidence"),"read supporting evidence").stream().map(DriverObservationEvidenceReader::reference).toList();
        var provenance=new ReadProvenance(kind,OpportunityJson.text(source.get("contract_id"),"contract_id"),OpportunityJson.text(source.get("request_id"),"request_id"),
                reference(source.get("original_receipt")),reference(source.get("definition_source")),reference(source.get("decoder_source")),
                ProposalLifecycleCodec.decodeObservation(OpportunityJson.toNode(source.get("source_frame"))),G2Wire.source(OpportunityJson.toNode(source.get("source"))),
                OpportunityJson.text(source.get("session_id"),"session_id"),OpportunityJson.integer(source.get("connection_generation"),"connection_generation"),
                optionalSequence(source,kind),OpportunityJson.object(source.get("arguments"),"read arguments"),support,
                kind.isRich()?OpportunityJson.array(source.get("component_receipts"),"rich component receipts").stream().map(DriverReadHistoryRowProducer::reference).toList():List.of(),
                kind.isRich()?Optional.of(DriverReadHistoryRichMaterial.PublicNumbers.fromJson(source.get("public_number_roles"))):Optional.empty());
        return new RawHistoryRow(OpportunityJson.integer(row.get("index"),"history index").longValueExact(),OpportunityJson.text(row.get("command"),"command"),
                OpportunityJson.bool(row.get("ok"),"ok"),OpportunityJson.object(row.get("result"),"normalized original result"),provenance);
    }
    /** Source header/closed fields and role DATA only; callers must restore identity roles then run the complete row decoder. */
    public static DriverReadHistoryRichMaterial.PublicNumbers publicNumbersFromSource(Value original) {
        Obj source=OpportunityJson.object(original,"original rich history source");Kind kind=requireSourceHeader(source);
        StrictJson.require(kind.isRich(),"only finite rich source kinds have source-owned public number roles");
        return DriverReadHistoryRichMaterial.PublicNumbers.fromJson(source.get("public_number_roles"));
    }
    private static Kind requireSourceHeader(Obj source) {
        var keys=new java.util.HashSet<>(Set.of("schema","kind","payload_field","contract_id","request_id","original_receipt","definition_source","decoder_source",
                "source_frame","source","session_id","connection_generation","arguments","supporting_evidence"));
        Kind kind=Kind.valueOf(OpportunityJson.text(source.get("kind"),"read kind"));if(kind.hasQuerySequence())keys.add("query_sequence");
        if(kind.isRich()){keys.add("component_receipts");keys.add("public_number_roles");}
        StrictJson.require(source.members().keySet().equals(keys)&&new Text(sourceSchema(kind)).equals(source.get("schema"))
                &&new Text(kind.payloadField()).equals(source.get("payload_field")),"original read source schema/field binding differs");
        return kind;
    }
    private static ExactRef reference(Value value){return DriverObservationEvidenceReader.reference(value);}
    /** Stable object ordering without changing original integer/decimal/null/array token domains. */
    private static Value ordered(Value value) {
        if(value instanceof Obj object) {
            var sorted=new java.util.TreeMap<String,Value>(object.members());var fields=new LinkedHashMap<String,Value>();
            sorted.forEach((key,item)->fields.put(key,ordered(item)));return new Obj(fields);
        }
        if(value instanceof Arr array)return new Arr(array.items().stream().map(DriverReadHistoryRowProducer::ordered).toList());
        return value;
    }
    private static IntegerValue integer(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static void unsigned(BigInteger value,boolean positive,String field){StrictJson.require(value!=null&&value.signum()>=(positive?1:0)&&value.compareTo(StrictJson.UINT64_MAX)<=0,field+" requires exact uint64");}
}
