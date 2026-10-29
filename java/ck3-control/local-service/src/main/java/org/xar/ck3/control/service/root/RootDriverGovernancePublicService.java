package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.governance.council.*;
import org.xar.ck3.control.governance.crownauthority.*;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.governance.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import org.xar.ck3.control.wave3.governance.crownfinalterms.CrownFinalTermsCodec;
import static org.xar.ck3.control.service.root.DriverGovernancePublicInput.*;
import static org.xar.ck3.control.service.root.DriverGovernancePublicProjection.Shape;

/** Explicit original driver business under the actual current Root, its held writer and installed native contracts. */
public final class RootDriverGovernancePublicService {
    private final RootRuntimeContext runtime;
    private final DriverGovernanceReadDefinitions definitions;
    private final RootRuntimeDefinitionModel.Build build;
    private final int maximumPolls;
    private final Optional<org.xar.ck3.control.contracts.ExactRef> publicCallerProducer;
    RootDriverGovernancePublicService(RootRuntimeContext runtime,DriverGovernanceReadDefinitions definitions,RootRuntimeDefinitionModel.Build build,int maximumPolls,Optional<org.xar.ck3.control.contracts.ExactRef> publicCallerProducer) {
        this.runtime=runtime;this.definitions=definitions;this.build=build;this.maximumPolls=maximumPolls;this.publicCallerProducer=java.util.Objects.requireNonNull(publicCallerProducer);
    }
    public RawJson council(Session same,Complete frame,GovernanceRuntimeInstaller.Installed installed,CouncilQuery input,boolean gates,Instant deadline)throws IOException,InterruptedException {
        revision(frame,input.expectedRevision(),false,"private council query revision mismatch");
        var first=gates?installed.privateReads().gates():installed.privateReads().query();
        var args=new OpportunityJson.Obj(java.util.Map.of()).with("position_key",new OpportunityJson.Text(input.position().key()));
        var initial=request(frame,first,args,deadline);
        return runtime.transport().withMailbox(deadline,scope->{
            PlanningReadReceipt terminal=mailbox(same,frame,first,args,installed.privateReads().status(),scope,deadline);
            var reply=CouncilPrivateCodec.decodeReply(terminal.original().originalResultToken().orElseThrow().bytes(),terminal.request().operation().value());
            StrictJson.require(reply instanceof CouncilPrivateCodec.Terminal,"actual terminal Council result required");
            CouncilPrivateCodec.requireTerminalBinding((CouncilPrivateCodec.Terminal)reply,first.operation().value(),PrivateCouncilReads.nativeFrame(initial));scope.complete(terminal.original());
            var normalized=CouncilPrivateCodec.normalize((CouncilPrivateCodec.Terminal)reply,first.operation().value(),PrivateCouncilReads.nativeFrame(initial),
                    GovernanceNativeReads.frame(initial),input.position(),build.gameVersion(),build.executableSha256());
            var raw=new RawJson(normalized.bytes());runtime.archive().withSession(same).preserveMaterial(raw);readQuotes.put(raw,new ReadQuote(runtime.archive().withSession(same).readReferenceOf(terminal),frame.identity()));return DriverGovernancePublicProjection.output(raw,Shape.COUNCIL);
        });
    }
    public RawJson crown(Session same,Complete frame,GovernanceRuntimeInstaller.Installed installed,Revision input,Instant deadline)throws IOException {
        revision(frame,input.expectedRevision(),false,"private crown-law read revision mismatch");var known=read(same,frame,installed.planningReads().crown(),new OpportunityJson.Obj(java.util.Map.of()),deadline);
        var raw=new RawJson(OpportunityJson.encode(known.value()));retainRead(same,raw,known,frame);return DriverGovernancePublicProjection.output(raw,Shape.CROWN);
    }
    public RawJson finalTerms(Session same,Complete frame,GovernanceRuntimeInstaller.Installed installed,Revision input,Instant deadline)throws IOException {
        revision(frame,input.expectedRevision(),false,"private realm-law query revision mismatch");var known=read(same,frame,installed.crownFinalTermsRead().contract(),new OpportunityJson.Obj(java.util.Map.of()),deadline);
        var raw=new RawJson(CrownFinalTermsCodec.encode(known.value().readback()));runtime.archive().withSession(same).preserveMaterial(raw);return DriverGovernancePublicProjection.output(raw,Shape.FINAL_TERMS);
    }
    public RawJson government(Session same,Complete frame,Revision input,Instant deadline)throws IOException {
        revision(frame,input.expectedRevision(),false,"government runtime adapter requires a living paused player");var known=read(same,frame,definitions.government(),new OpportunityJson.Obj(java.util.Map.of()),deadline);
        runtime.archive().withSession(same).preserveMaterial(known.value());return DriverGovernancePublicProjection.output(known.value(),Shape.GOVERNMENT);
    }
    private <T> PlanningReadResult.Known<T> read(Session same,Complete frame,ReadContract<T> contract,OpportunityJson.Obj args,Instant deadline)throws IOException {
        runtime.writer().requireSession(same);var request=request(frame,contract,args,deadline);var result=runtime.reads().read(same,contract,request);
        if(result instanceof PlanningReadResult.Unavailable<T> unavailable) {
            if(unavailable.original().isPresent()&&unavailable.original().orElseThrow() instanceof NativeActionPort.AckReceived ack&&staleRejection(ack,request,contract)) {
                var archive=runtime.archive().withSession(same);var original=archive.preserve(ack);StrictJson.require(archive.load(original).equals(ack),"actual rejected READ original changed during retention");
                throw new StaleReadRejected(this,request,original,ack,readBinding(frame));
            }
            throw failure(unavailable.reason());
        }
        var known=(PlanningReadResult.Known<T>)result;
        StrictJson.require(known.receipt().request().equals(request)&&known.receipt().contractId().equals(contract.contractId())
                &&runtime.archive().withSession(same).readReferenceOf(known.receipt()).equals(known.originalReceipt()),"public driver result lost its installed contract/original archive");
        GovernanceNativeReads.verifyGuards(known.receipt());return known;
    }
    private static final Set<String> STALE_DIFF_FIELDS=Set.of("date_raw","speed","paused","player_id","map_ready","has_played_character","played_character_id","played_character_alive","played_character_stress_points","played_character_gold","played_character_prestige","played_character_piety","played_character_betrothed_id","played_character_primary_spouse_id","played_character_spouse_ids","has_active_event","active_event_instance_id","active_event_option_count","has_pending_character_interaction","pending_character_interaction_id","pending_sender_character_id","pending_auto_accept_notification","active_wars","player_armies","has_one_life_settlement","one_life_settlement","played_character_event_trait_membership","unlisted_snapshot_field");
    /** Pure packet classification only. A true value mints no Root/read/refresh authority. */
    static boolean staleRejection(NativeActionPort.AckReceived ack,PlanningReadRequest request,ReadContract<?> installed) {
        if(!(request.origin() instanceof CommandOrigin.Gameplay)||installed.guardMode()!=ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP)return false;
        String operation=request.operation().value();
        if(!Set.of(CouncilPrivateCodec.QUERY,CouncilPrivateCodec.GATES,GovernancePlanningReads.CROWN).contains(operation)
                ||!installed.operation().equals(request.operation())||installed.permissionMode()!=ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE
                ||installed.wireProfile()!=ReadContract.WireProfile.EXECUTE_STEP||ack.nativeOk()||ack.outbound().isEmpty()
                ||request.before().frame().identity().nativeRevision().signum()<=0)return false;
        try {
            var decoded=NativeWire.decode(ack.originalPacket());
            if(!(decoded instanceof NativeWire.CommandResult result)||result.nativeOk()||!result.requestId().equals(ack.requestId())
                    ||result.result().presence()!=NativeWire.Presence.ABSENT||result.error().presence()!=NativeWire.Presence.VALUE)return false;
            var frame=StrictJson.object(StrictJson.parse(result.payload().value()),Set.of("type","protocol_version","request_id","ok","error"));
            if(!frame.equals(StrictJson.parse(ack.originalFrame().bytes()))||ack.originalResultToken().isPresent())return false;
            var wire=NativeWire.decodeExecuteRequest(ack.outbound().orElseThrow().originalPacket());
            if(!wire.requestId().equals(ack.requestId())||!wire.step().equals(operation)||wire.expectedSnapshotRevision().isPresent()
                    ||wire.expectedRevision().filter(request.before().frame().identity().nativeRevision()::equals).isEmpty())return false;
            var fields=CouncilCodec.object(StrictJson.parse(wire.normalizedAdditionalFields().value()));
            if(operation.equals(GovernancePlanningReads.CROWN)) {
                StrictJson.object(fields,Set.of("expected_date_raw","expected_player_character_id"));
                if(!StrictJson.integer(fields.get("expected_date_raw"),BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).equals(request.before().frame().identity().dateRaw())
                        ||!StrictJson.integer(fields.get("expected_player_character_id"),BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE)).equals(request.before().frame().identity().player())
                        ||!request.arguments().members().isEmpty())return false;
            }else {
                StrictJson.object(fields,Set.of("position_key"));var args=CouncilCodec.object(StrictJson.parse(OpportunityJson.encode(request.arguments())));StrictJson.object(args,Set.of("position_key"));
                if(!fields.equals(args))return false;CouncilModels.Position.exact(CouncilCodec.text(fields,"position_key"));
            }
            String error=CouncilCodec.text(frame,"error"),legacy="nonwar private snapshot revision is stale or malformed";
            if(error.length()>8192)return false;if(error.equals(legacy))return true;
            var match=java.util.regex.Pattern.compile(java.util.regex.Pattern.quote(legacy)+": cause=(revision_mismatch|full_snapshot_changed) expected_revision=(0|[1-9][0-9]{0,19}) native_revision=(0|[1-9][0-9]{0,19})(.*)").matcher(error);
            if(!match.matches())return false;
            BigInteger expected=new BigInteger(match.group(2)),actual=new BigInteger(match.group(3));
            if(!expected.equals(request.before().frame().identity().nativeRevision())||actual.compareTo(NativeWire.UINT64_MAX)>0)return false;
            if(match.group(1).equals("revision_mismatch"))return match.group(4).isEmpty()&&actual.compareTo(expected)>0;
            String suffix=" changed_snapshot_fields=";
            if(!actual.equals(expected)||!match.group(4).startsWith(suffix))return false;
            var fieldsChanged=StrictJson.parse(match.group(4).substring(suffix.length()).getBytes(java.nio.charset.StandardCharsets.UTF_8));
            if(!fieldsChanged.isArray()||fieldsChanged.isEmpty()||fieldsChanged.size()>64)return false;
            var unique=new java.util.HashSet<String>();
            for(var field:fieldsChanged)if(!field.isTextual()||!STALE_DIFF_FIELDS.contains(field.textValue())||!unique.add(field.textValue()))return false;
            return true;
        }catch(IOException|IllegalArgumentException rejected) {return false;}
    }
    /** The original Council _binding is deliberately distinct from Crown's native-revision gate.
     * This immutable DATA comparison never supplies a rejected ACK, source permission or Root lease. */
    record ReadBinding(String snapshotId,BigInteger publicRevision,BigInteger nativeRevision,BigInteger dateRaw,
            boolean paused,boolean mapReady,BigInteger player,boolean alive) {
        ReadBinding {StrictJson.text(snapshotId);java.util.Objects.requireNonNull(publicRevision);java.util.Objects.requireNonNull(nativeRevision);java.util.Objects.requireNonNull(dateRaw);java.util.Objects.requireNonNull(player);}
    }
    static ReadBinding readBinding(Complete actual) {
        var semantic=actual.semantic();var played=OpportunityJson.object(semantic.get("played_character"),"played_character");
        var frame=actual.identity().frame();
        return new ReadBinding(frame.snapshotId(),frame.revision(),frame.identity().nativeRevision(),frame.identity().dateRaw(),
                OpportunityJson.bool(semantic.get("paused"),"paused"),OpportunityJson.bool(semantic.get("map_ready"),"map_ready"),
                OpportunityJson.integer(played.get("character_id"),"character_id"),OpportunityJson.bool(played.get("alive"),"alive"));
    }
    static boolean freshReadBinding(OperationKey operation,ReadBinding before,ReadBinding after) {
        java.util.Objects.requireNonNull(before);java.util.Objects.requireNonNull(after);
        if(operation.value().equals(GovernancePlanningReads.CROWN))return after.nativeRevision().compareTo(before.nativeRevision())>0;
        StrictJson.require(Set.of(CouncilPrivateCodec.QUERY,CouncilPrivateCodec.GATES).contains(operation.value()),"only original Council/Crown READs have stale-frame retry policy");
        return !after.equals(before);
    }
    /** Only this service's actual installed, qualified READ call can mint this retained rejection. It is never persisted as submit authority. */
    static final class StaleReadRejected extends RuntimeException {
        private static final long serialVersionUID=1L;
        private final transient RootDriverGovernancePublicService owner;
        private final transient PlanningReadRequest request;
        private final transient org.xar.ck3.control.contracts.ExactRef original;
        private final transient NativeActionPort.AckReceived ack;
        private final transient ReadBinding binding;
        private StaleReadRejected(RootDriverGovernancePublicService owner,PlanningReadRequest request,org.xar.ck3.control.contracts.ExactRef original,NativeActionPort.AckReceived ack,ReadBinding binding) {
            super((request.operation().value().equals(GovernancePlanningReads.CROWN)?"private crown-law native RED: ":"")+CouncilCodec.text(CouncilCodec.object(StrictJson.parse(ack.originalFrame().bytes())),"error"));
            this.owner=owner;this.request=request;this.original=original;this.ack=ack;this.binding=binding;
        }
        boolean newer(RootDriverGovernancePublicService actual,Session same,Complete frame)throws IOException {
            StrictJson.require(actual==owner&&frame.identity().game().equals(request.before().game())&&frame.sessionId().equals(request.sessionId())&&frame.identity().frame().identity().player().equals(request.before().frame().identity().player())&&java.util.Objects.equals(frame.identity().frame().episodeRunId(),request.before().frame().episodeRunId()),"stale READ cannot cross its original service, physical Game or session");
            actual.runtime.writer().requireSession(same);StrictJson.require(actual.runtime.archive().withSession(same).load(original).equals(ack),"retained rejected READ packet/outbound identity changed");
            return freshReadBinding(request.operation(),binding,readBinding(frame));
        }
        PublicServiceFailure unavailable() {return failure(getMessage());}
    }
    private static PlanningReadRequest request(Complete frame,ReadContract<?> contract,OpportunityJson.Obj args,Instant deadline) {
        return new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),contract.operation(),args,deadline);
    }
    private PlanningReadReceipt mailbox(Session same,Complete frame,ReadContract<?> first,OpportunityJson.Obj args,ReadContract<?> status,NativeGameTransport.MailboxScope scope,Instant deadline)throws IOException,InterruptedException {
        PlanningReadReceipt current;
        try {current=read(same,frame,first,args,deadline).receipt();}
        catch(StaleReadRejected rejected) {scope.complete(rejected.ack);throw rejected;}
        for(int count=0;;count++) {
            var value=CouncilCodec.object(StrictJson.parse(current.original().originalResultToken().orElseThrow().bytes()));
            if(!value.has("private_council_transport")) {return current;}
            StrictJson.trueValue(value.get("private_council_transport"));StrictJson.require(!CouncilCodec.bool(value.get("advertised"))&&CouncilCodec.text(value,"status").equals("pending"),"private council mailbox has no completed operation");
            if(count>=maximumPolls||!runtime.clock().instant().isBefore(deadline))throw failure("private council operation result timed out; pending read is retained and never requeued");
            Thread.sleep(1);current=read(same,frame,status,new OpportunityJson.Obj(java.util.Map.of()),deadline).receipt();
        }
    }
    public ActionCommand prepareEnact(Session same,Complete frame,CrownEnact input,Instant deadline)throws IOException {
        var raw=DriverGovernancePublicProjection.input(input.readback(),Shape.CROWN);original(same,raw);
        var readback=CrownAuthorityCodec.decodeReadback(raw.bytes());source(frame,readback.sourceFrame());CrownCallerSelection.select(readback,input.lawKey());
        var args=StrictJson.object().put("law_key",input.lawKey()).put("caller_request_id",input.actionId());args.set("readback",StrictJson.parse(raw.bytes()));
        var limits=args.putObject("caller_budgets");for(var amount:input.budgets())limits.put(amount.currency().wire(),amount.raw());
        return command(frame,GovernanceActionPreparation.CROWN,input.actionId(),args,
                List.of(new ProposalLifecycle.ExpectedText(new ProposalLifecycle.FieldKey("crown.effective_law_key"),input.lawKey())),Set.of(frame.identity().frame().identity().player()),deadline);
    }
    public RawJson presentEnact(Session same,ActionReceipt receipt)throws IOException {
        requireReceipt(same,receipt,GovernanceActionPreparation.CROWN);
        var args=CouncilCodec.object(StrictJson.parse(OpportunityJson.encode(receipt.command().arguments())));
        var readback=CrownAuthorityCodec.decodeReadback(StrictJson.canonical(args.get("readback")));String actionId=CouncilCodec.text(args,"caller_request_id"),lawKey=CouncilCodec.text(args,"law_key");
        var result=crownAck(receipt);crownEnvelope(result,GovernanceActionPreparation.CROWN,false);
        var value=CouncilCodec.object(result.get("ack")).deepCopy();StrictJson.require(CouncilCodec.text(value,"submitted_request_id").equals(actionId),"actual crown ACK changed caller identity");
        String status=CouncilCodec.text(result,"status");StrictJson.require(Set.of("submitted_verification_pending","rejected_before_submit").contains(status),"private crown-law submit result malformed");
        if(status.equals("submitted_verification_pending"))requireCrownPendingAck(value,readback,lawKey);
        value.put("schema","realm-law-crown-formal-private-v1").put("status",status).put("material_result",false);provenance(value);
        var retained=raw(value);runtime.archive().withSession(same).preserveMaterial(retained);return DriverGovernancePublicProjection.output(retained,Shape.CROWN);
    }
    public RawJson crownReceipt(Session same,Complete frame,CrownReceipt input,Instant deadline)throws IOException {
        revision(frame,input.expectedRevision(),false,"private crown-law receipt identity is invalid");
        var candidates=runtime.readCatalog().contracts().stream().filter(contract->contract.operation().value().equals("verify-realm-law-crown-v1-private")).toList();
        StrictJson.require(candidates.size()==1,"exact Root-installed crown receipt contract required");
        var args=new OpportunityJson.Obj(java.util.Map.of()).with("submitted_request_id",new OpportunityJson.Text(input.submittedRequestId())).with("expected_date_raw",new OpportunityJson.IntegerValue(frame.identity().frame().identity().dateRaw())).with("expected_player_character_id",new OpportunityJson.IntegerValue(frame.identity().frame().identity().player()));
        var known=read(same,frame,candidates.getFirst(),args,deadline);var result=CouncilCodec.object(StrictJson.parse(known.receipt().original().originalResultToken().orElseThrow().bytes()));
        crownEnvelope(result,"verify-realm-law-crown-v1-private",true);String status=CouncilCodec.text(result,"status");
        StrictJson.require(Set.of("enacted","failed").contains(status),"private crown-law receipt malformed");var value=CouncilCodec.object(result.get("receipt")).deepCopy();
        StrictJson.require(CouncilCodec.text(value,"submitted_request_id").equals(input.submittedRequestId()),"private crown-law receipt identity changed");
        if(status.equals("enacted")) {
            for(String flag:List.of("effective_law_verified","resources_verified","succession_verified"))StrictJson.trueValue(value.get(flag));
            StrictJson.require(CouncilCodec.u64(value.get("post_public_revision"),true).equals(frame.identity().frame().identity().nativeRevision())
                    &&CouncilCodec.number(value,"post_date_raw",Integer.MIN_VALUE,Integer.MAX_VALUE)==frame.identity().frame().identity().dateRaw().intValueExact(),"private crown-law enacted receipt lacks material verification");
            CouncilCodec.text(value,"effective_law_key");org.xar.ck3.control.application.effects.NativeGovernanceEffects.validateTitles(value.get("title_successors"));
        }
        value.put("schema","realm-law-crown-formal-private-v1").put("status",status).put("material_result",status.equals("enacted"));provenance(value);
        return DriverGovernancePublicProjection.output(raw(value),Shape.CROWN);
    }
    public ActionCommand prepareAssign(Session same,Complete frame,GovernanceRuntimeInstaller.Installed installed,CouncilAssign input,Instant deadline)throws IOException,InterruptedException {
        revision(frame,input.expectedRevision(),true,"private council submit revision changed");
        var caller=DriverGovernancePublicProjection.input(input.query(),Shape.COUNCIL);original(same,caller);var quoted=CouncilCodec.object(StrictJson.parse(caller.bytes()));
        var source=CouncilCodec.object(quoted.get("source_frame"));StrictJson.require(source.equals(sourceFrame(frame))&&CouncilCodec.text(quoted,"status").equals("available"),"private council assignment lacks its current native query");
        var payload=CouncilCodec.object(quoted.get("council_composition_candidates"));var role=CouncilModels.Position.exact(CouncilCodec.text(CouncilCodec.object(payload.get("position")),"position_key"));
        var explicit=DriverGovernancePublicInput.explicitCouncilId(input.actionId());
        if(explicit.isPresent()) {
            var quotedCandidates=CouncilCodec.decode(StrictJson.canonical(payload),PrivateCouncilReads.nativeFrame(request(frame,installed.privateReads().gates(),new OpportunityJson.Obj(java.util.Map.of()),deadline)),role);
            CouncilActionCodec.request(quotedCandidates,input.candidateCharacterId(),explicit.orElseThrow());
            if(publicCallerProducer.isEmpty())throw failure("explicit private Council native request identity lacks its actual installed source producer; caller identity retained, no submission occurred");
        }
        var freshPublic=council(same,frame,installed,new CouncilQuery(input.expectedRevision(),role),true,deadline);
        var fresh=DriverGovernancePublicProjection.input(freshPublic,Shape.COUNCIL);var query=CouncilCodec.object(StrictJson.parse(fresh.bytes()));
        StrictJson.require(query.get("council_composition_candidates").equals(payload),"private council quoted candidates changed before fresh final gates");
        var candidates=CouncilCodec.decode(StrictJson.canonical(payload),PrivateCouncilReads.nativeFrame(request(frame,installed.privateReads().gates(),new OpportunityJson.Obj(java.util.Map.of()),deadline)),role);
        var primitive=CouncilActionCodec.request(candidates,input.candidateCharacterId(),"public-council-validation");
        var fields=StrictJson.object().put("position_key",role.key()).put("candidate_character_id",input.candidateCharacterId())
                .put("expected_has_incumbent",primitive.incumbentId().isPresent()).put("expected_incumbent_character_id",primitive.incumbentId().orElse(-1));fields.set("original_query",query);fields.put("public_submission_schema",CouncilCallerSubmission.SCHEMA);if(explicit.isPresent())fields.put("caller_request_id",explicit.orElseThrow());else fields.putNull("caller_request_id");
        String identity=explicit.orElseGet(()->"council-assign-"+java.util.UUID.randomUUID().toString().replace("-",""));
        return command(frame,CouncilActionCodec.PRIVATE_ASSIGN,identity,fields,
                List.of(new ProposalLifecycle.ExpectedText(new ProposalLifecycle.FieldKey("council.position_key"),role.key()),
                        new ProposalLifecycle.ExpectedInteger(new ProposalLifecycle.FieldKey("council.incumbent_character_id"),BigInteger.valueOf(input.candidateCharacterId()))),
                Set.of(BigInteger.valueOf(input.candidateCharacterId())),deadline);
    }
    public RawJson presentAssign(Session same,GovernanceRuntimeInstaller.Installed installed,ActionReceipt receipt)throws IOException {
        requireReceipt(same,receipt,CouncilActionCodec.PRIVATE_ASSIGN);return councilAck(same,installed,receipt);
    }
    public RawJson councilReceipt(Session same,Complete frame,GovernanceRuntimeInstaller.Installed installed,CouncilReceipt input,Instant deadline)throws IOException,InterruptedException {
        revision(frame,input.expectedRevision(),true,"private council receipt revision changed");
        var raw=DriverGovernancePublicProjection.input(input.pending(),Shape.COUNCIL);var pending=CouncilCodec.object(StrictJson.parse(raw.bytes()));
        var expected=pendingAck(pending);var before=frame.identity().frame().identity();
        StrictJson.require(expected.status()==CouncilActionCodec.AckStatus.HELPER_INVOKED_VERIFICATION_PENDING&&before.nativeRevision().compareTo(expected.request().frame().nativeRevision())>0
                &&before.player().intValueExact()==expected.request().frame().ownerId(),"private council receipt lacks an independent later owner frame");
        var exact=CouncilCodec.object(pending.get("exact_build"));StrictJson.require(CouncilCodec.text(exact,"game_version").equals(build.gameVersion())&&CouncilCodec.text(exact,"executable_sha256").equalsIgnoreCase(build.executableSha256()),"private council receipt exact build differs");
        return runtime.transport().withMailbox(deadline,scope->{
            var terminal=mailbox(same,frame,definitions.councilReceipt(),new OpportunityJson.Obj(java.util.Map.of()),installed.privateReads().status(),scope,deadline);
            var result=CouncilCodec.object(StrictJson.parse(terminal.original().originalResultToken().orElseThrow().bytes()));
            StrictJson.require(CouncilCodec.text(result,"schema").equals("xar.ck3.council-application-main/v1")&&CouncilCodec.text(result,"step").equals(CouncilActionCodec.RECEIPT),"private council result lacks an incumbent receipt");StrictJson.trueValue(result.get("accepted"));
            var receipt=CouncilActionCodec.decodeReceipt(StrictJson.canonical(result.get("council_assign_councillor_receipt")),expected);
            StrictJson.require(CouncilCodec.text(result,"status").equals(CouncilCodec.text(CouncilCodec.object(result.get("council_assign_councillor_receipt")),"status")),"private council status disagrees with incumbent receipt");
            if(receipt.status()==CouncilActionCodec.ReceiptStatus.APPLIED)StrictJson.require(receipt.postSnapshotId().equals("native:"+before.nativeRevision())&&receipt.postPublicRevision().equals(before.nativeRevision())
                    &&receipt.postNativeRevision().equals(before.nativeRevision())&&receipt.postDateRaw()==before.dateRaw().intValueExact(),"private council receipt does not match its current native frame");
            scope.complete(terminal.original());result.put("step",CouncilActionCodec.PRIVATE_RECEIPT).put("native_step",CouncilActionCodec.RECEIPT).put("private_build",true).put("advertised",false)
                    .put("action_request_id",expected.request().requestId());result.set("source_frame",sourceFrame(frame));result.set("exact_build",pending.get("exact_build"));
            return DriverGovernancePublicProjection.output(raw(result),Shape.COUNCIL);
        });
    }
    private RawJson councilAck(Session same,GovernanceRuntimeInstaller.Installed installed,ActionReceipt receipt)throws IOException {
        var candidates=new ArrayList<ObjectNode>();receipt.ack().filter(value->value.nativeOk()&&value.originalResultToken().isPresent())
                .ifPresent(value->candidates.add(CouncilCodec.object(StrictJson.parse(value.originalResultToken().orElseThrow().bytes()))));
        for(var retained:installed.continuations().retained(same))if(retained.request().scope().parentActionId().equals(receipt.command().actionId())
                &&retained.request().scope().parentBodySha256().equals(receipt.bodySha256())&&retained.entry().outcome().isPresent()) {
            var outcome=runtime.archive().withSession(same).load(retained.entry().outcome().orElseThrow());
            if(outcome instanceof NativeActionPort.AckReceived value&&value.nativeOk()&&value.originalResultToken().isPresent())candidates.add(CouncilCodec.object(StrictJson.parse(value.originalResultToken().orElseThrow().bytes())));
        }
        var matches=candidates.stream().filter(value->value.has("council_assign_councillor_ack")).toList();
        if(matches.isEmpty())throw new PublicServiceFailure(PublicServiceFailure.Kind.exact("StepPostconditionError"),"private council submission result unavailable; action state unknown",Optional.empty());
        var result=matches.getFirst().deepCopy();StrictJson.require(matches.stream().allMatch(result::equals),"conflicting actual Council ACK originals retained; do not replay");
        StrictJson.require(CouncilCodec.text(result,"schema").equals("xar.ck3.council-application-main/v1")&&CouncilCodec.text(result,"step").equals(CouncilActionCodec.ASSIGN),"private council submit lacks its native ACK");StrictJson.trueValue(result.get("accepted"));
        var ack=CouncilCodec.object(result.get("council_assign_councillor_ack"));StrictJson.require(CouncilCodec.text(result,"status").equals(CouncilCodec.text(ack,"status")),"private council submit status disagrees with its ACK");String nativeId=CouncilCodec.text(ack,"action_request_id");
        var request=GovernanceActionPreparation.councilRequest(receipt.command(),nativeId);CouncilActionCodec.decodeAck(StrictJson.canonical(ack),request);
        result.put("step",CouncilActionCodec.PRIVATE_ASSIGN).put("native_step",CouncilActionCodec.ASSIGN).put("private_build",true).put("advertised",false).put("action_request_id",nativeId);
        result.set("request",CouncilActionCodec.wireFields(request,false));result.set("source_frame",sourceFrame(receipt.command().before()));
        result.set("exact_build",StrictJson.object().put("game_version",build.gameVersion()).put("executable_sha256",build.executableSha256()));
        var raw=raw(result);runtime.archive().withSession(same).preserveMaterial(raw);return DriverGovernancePublicProjection.output(raw,Shape.COUNCIL);
    }
    static void requireCrownPendingAck(ObjectNode value,CrownAuthorityPolicy.Readback readback,String selectedLaw) {
        var original=readback.sourceFrame();StrictJson.trueValue(value.get("verification_pending"));
        StrictJson.require(CouncilCodec.id(value.get("player_character_id"))==original.playerCharacterId().intValueExact()
                &&CouncilCodec.text(value,"requested_law_key").equals(selectedLaw)&&CouncilCodec.text(value,"group_key").equals(readback.groupKey())
                &&CouncilCodec.u64(value.get("pre_public_revision"),true).equals(original.queriedNativeRevision())
                &&BigInteger.valueOf(CouncilCodec.number(value,"pre_date_raw",Integer.MIN_VALUE,Integer.MAX_VALUE)).equals(original.dateRaw()),"private crown-law submit ACK identity malformed");
        org.xar.ck3.control.application.effects.NativeGovernanceEffects.validateTitles(value.get("title_successors"));
    }
    private static CouncilActionCodec.Ack pendingAck(ObjectNode pending) {
        var ack=CouncilCodec.object(pending.get("council_assign_councillor_ack"));boolean incumbent=CouncilCodec.bool(ack.get("had_incumbent"));
        int previous=(int)CouncilCodec.number(ack,"previous_incumbent_character_id",-1,Integer.MAX_VALUE);
        var frame=new CouncilModels.Frame(CouncilCodec.text(ack,"pre_snapshot_id"),CouncilCodec.u64(ack.get("pre_public_revision"),true),CouncilCodec.u64(ack.get("pre_native_revision"),true),
                (int)CouncilCodec.number(ack,"pre_date_raw",Integer.MIN_VALUE,Integer.MAX_VALUE),CouncilCodec.id(ack.get("owner_character_id")));
        var request=new CouncilActionCodec.Request(CouncilCodec.text(ack,"action_request_id"),frame,CouncilModels.Position.exact(CouncilCodec.text(ack,"position_key")),
                CouncilCodec.id(ack.get("candidate_character_id")),incumbent?OptionalInt.of(previous):OptionalInt.empty());
        return CouncilActionCodec.decodeAck(StrictJson.canonical(ack),request);
    }
    private ActionCommand command(Complete frame,String operation,String nativeIdentity,ObjectNode fields,List<ProposalLifecycle.ExpectedValue> values,Set<BigInteger> characters,Instant deadline) {
        return produceCommand(frame,operation,nativeIdentity,fields,values,characters,deadline,publicCallerProducer);
    }
    /** Shared DATA producer; source qualification and native preparation remain with the actual installed caller. */
    static ActionCommand produceCommand(Complete frame,String operation,String nativeIdentity,ObjectNode fields,List<ProposalLifecycle.ExpectedValue> values,Set<BigInteger> characters,Instant deadline,Optional<org.xar.ck3.control.contracts.ExactRef> publicCallerProducer) {
        java.util.Objects.requireNonNull(publicCallerProducer);
        String actionId="public-governance-"+ActionCodec.sha256((frame.identity().game().toString()+operation+nativeIdentity).getBytes(java.nio.charset.StandardCharsets.UTF_8));
        var expected=new ProposalLifecycle.ExpectedPostcondition(ProposalLifecycle.POSTCONDITION_VERSION,frame.identity(),frame.source(),"xar.java.governance-independent-effect/v1",values);
        var arguments=OpportunityJson.parse(StrictJson.canonical(fields));StrictJson.require(arguments instanceof OpportunityJson.Obj,"typed public action object required");
        ProtocolRequestIdentity protocolIdentity=ProtocolRequestIdentity.BodyDerived.INSTANCE;
        if(operation.equals(CouncilActionCodec.PRIVATE_ASSIGN)) {
            var caller=CouncilCallerSubmission.requestedId(fields);
            if(caller.isPresent())protocolIdentity=new ExplicitOriginalProtocolId(ExplicitOriginalProtocolId.Contract.PUBLIC_COUNCIL_ASSIGNMENT,caller.orElseThrow(),publicCallerProducer.orElseThrow(()->failure("actual installed Council caller producer is unavailable")));
        }
        var command=new ActionCommand(actionId,new CommandOrigin.Gameplay(frame.identity()),frame.source(),frame.sessionId(),new OperationKey(operation),(OpportunityJson.Obj)arguments,new CommandExpectation.Gameplay(expected),
                new JointBudgetSelector.Claims(Set.of(),Set.of(),characters,Set.of()),deadline,protocolIdentity);
        return command;
    }
    private final java.util.Map<RawJson,ReadQuote> readQuotes=new java.util.HashMap<>();
    private record ReadQuote(org.xar.ck3.control.contracts.ExactRef receipt,org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity frame) { }
    private void retainRead(Session same,RawJson raw,PlanningReadResult.Known<?> known,Complete frame)throws IOException {
        runtime.writer().requireSession(same);runtime.archive().withSession(same).preserveMaterial(raw);readQuotes.put(raw,new ReadQuote(known.originalReceipt(),frame.identity()));
    }
    private void original(Session same,RawJson raw)throws IOException {
        runtime.writer().requireSession(same);var retained=readQuotes.get(raw);
        StrictJson.require(retained!=null,"caller quote has no actual current-Game installed read custody; query it again, no submission occurred");
        var original=runtime.archive().withSession(same).loadRead(retained.receipt());
        StrictJson.require(original.request().before().equals(retained.frame())&&retained.frame().game().equals(runtime.game().generation()),"caller quote lost its actual physical-Game read origin");
        RootGuardEvidence.requireHistory(original.before().binding(),runtime.archive().withSession(same),same);RootGuardEvidence.requireHistory(original.after().binding(),runtime.archive().withSession(same),same);
    }
    /** Original Crown presenter error only; the canonical UNKNOWN receipt is retained unchanged. */
    static ObjectNode crownAck(ActionReceipt receipt) {
        StrictJson.require(receipt.command().operation().value().equals(GovernanceActionPreparation.CROWN),"Crown original result presenter requires its exact operation");
        if(receipt.ack().isEmpty())throw failure("private crown-law command_result unavailable");
        return ack(receipt);
    }
    private static ObjectNode ack(ActionReceipt receipt) {
        var ack=receipt.ack().orElseThrow(()->failure("native action result unavailable; canonical UNKNOWN retained, never resubmit"));
        StrictJson.require(ack.nativeOk()&&ack.originalResultToken().isPresent(),"native action ACK unavailable; canonical state retained");return CouncilCodec.object(StrictJson.parse(ack.originalResultToken().orElseThrow().bytes()));
    }
    private void crownEnvelope(ObjectNode result,String step,boolean readOnly) {
        StrictJson.object(result,Set.of("step","accepted","private_build","advertised","backend_id","game_version","executable_sha256","read_only","status","observation","ack","receipt"));
        StrictJson.require(CouncilCodec.text(result,"step").equals(step)&&CouncilCodec.text(result,"game_version").equals(build.gameVersion())
                &&CouncilCodec.text(result,"executable_sha256").equalsIgnoreCase(build.executableSha256()),"actual crown envelope source changed");
        for(String field:List.of("accepted","private_build"))StrictJson.trueValue(result.get(field));StrictJson.require(!CouncilCodec.bool(result.get("advertised"))&&CouncilCodec.bool(result.get("read_only"))==readOnly,"actual crown envelope permission phase changed");
        StrictJson.require(CouncilCodec.text(result,"backend_id").equals("native-headless")&&result.get("observation").isNull()
                &&(readOnly?result.get("ack").isNull():result.get("receipt").isNull()),"actual crown envelope mixed its source or action/receipt phases");
    }
    private void source(Complete frame,CrownAuthorityPolicy.SourceFrame original) {
        var actual=frame.identity().frame();var id=actual.identity();
        StrictJson.require(original.queriedSnapshotId().equals(actual.snapshotId())&&original.queriedRevision().equals(actual.revision())&&original.queriedNativeRevision().equals(id.nativeRevision())
                &&original.playerCharacterId().equals(id.player())&&original.dateRaw().equals(id.dateRaw())&&original.exactCk3Build().equals(build.gameVersion())
                &&original.exeSha256().equalsIgnoreCase(build.executableSha256()),"private crown-law submit lacks its observed paused source");
    }
    private void provenance(ObjectNode node) {node.put("exact_ck3_build",build.gameVersion());if(!build.gameVersion().equals("1.19.0.6"))node.put("exe_sha256",build.executableSha256());}
    private void requireReceipt(Session same,ActionReceipt receipt,String operation)throws IOException {
        runtime.writer().requireSession(same);StrictJson.require(receipt.command().operation().value().equals(operation)&&receipt.command().before().game().equals(runtime.game().generation()),"public governance result crossed the actual operation or physical Game");
        var archive=runtime.archive().withSession(same);var original=archive.receiptReferenceOf(receipt);StrictJson.require(archive.loadReceipt(original).equals(receipt),"public governance result lost its exact original archived receipt");
    }
    private static ObjectNode sourceFrame(Complete frame) {return sourceFrame(frame.identity());}
    private static ObjectNode sourceFrame(ProposalLifecycle.ObservationIdentity before) {
        var observed=before.frame();var id=observed.identity();return StrictJson.object().put("snapshot_id",observed.snapshotId()).put("revision",observed.revision())
                .put("native_revision",id.nativeRevision()).put("date_raw",id.dateRaw()).put("player_character_id",id.player()).put("paused",true);
    }
    private static void revision(Complete frame,BigInteger expected,boolean submission,String message) {
        if(!frame.identity().frame().revision().equals(expected))throw new PublicServiceFailure(submission?PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH:PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,message,Optional.empty());
    }
    private static PublicServiceFailure failure(String message) {return new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,message,Optional.empty());}
    private static RawJson raw(ObjectNode node) {return new RawJson(StrictJson.canonical(node));}
}
