package org.xar.ck3.control.nativebridge.capabilities.religion;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionService;
import static org.xar.ck3.control.nativebridge.capabilities.religion.ReligionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.religion.ReligionModels.*;

/** Original conversion/County algorithms on the existing sole writer and independent native reads. */
public final class ReligionConversionActions {
    public enum Kind {
        CONVERSION("ck3_convert_player_religion_private_v1","submit-player-religion-conversion-private-v1","query-player-religion-conversion-result-private-v1"),
        COUNTY("ck3_submit_county_conversion_task","county-conversion-task-submit-private-v1","county-conversion-task-result-private-v1");
        private final String method,step,resultStep;
        Kind(String method,String step,String resultStep){this.method=method;this.step=step;this.resultStep=resultStep;}
        public String method(){return method;}public OperationKey operation(){return new OperationKey(step);}public OperationKey resultOperation(){return new OperationKey(resultStep);}
        public String observer(){return this==CONVERSION?"xar.java.religion-conversion-material/v1":"xar.java.county-conversion-assignment/v1";}
    }
    /** DATA from the original packet; a constructor grants no submission permission. */
    public sealed interface Submission permits ConversionSubmission,CountySubmission {
        Kind kind();RawJson envelope();RawJson originalOwner();PlayerReligionContext.Build build();SubmitStatus status();boolean copyCalled();String requestId();String actionId();
    }
    public record ConversionSubmission(ReligionOwner owner,RawJson envelope,RawJson originalOwner,PlayerReligionContext.Build build) implements Submission {
        public Kind kind(){return Kind.CONVERSION;}public SubmitStatus status(){return owner.status();}public boolean copyCalled(){return owner.submitCopyCalled();}
        public String requestId(){return owner.requestId().value();}public String actionId(){return owner.request().actionId().value();}
    }
    public record CountySubmission(CountyOwner owner,RawJson envelope,RawJson originalOwner,PlayerReligionContext.Build build) implements Submission {
        public Kind kind(){return Kind.COUNTY;}public SubmitStatus status(){return owner.status();}public boolean copyCalled(){return owner.submitCopyCalled();}
        public String requestId(){return owner.requestId().value();}public String actionId(){return owner.request().actionId().value();}
    }
    @FunctionalInterface public interface ResultPort { PlanningReadReceipt read(ActionCommand command,ActionState.Attempt attempt,Complete actualAfter); }
    private final Kind kind;
    private final ReligionCapabilities.Registration original;
    private final ReadContract<?> gameplay,reconciliation;
    private final NativeEffectSnapshots snapshots;
    private final Supplier<ActionPorts.OutcomeArchive> archives;
    private final NativeEffectEvidence.FrameLoader frames;
    private final ResultPort results;
    public ReligionConversionActions(Kind kind,ReligionCapabilities.Registration original,ReadContract<?> gameplay,ReadContract<?> reconciliation,
            NativeEffectSnapshots snapshots,Supplier<ActionPorts.OutcomeArchive> archives,NativeEffectEvidence.FrameLoader frames,ResultPort results) {
        this.kind=Objects.requireNonNull(kind);this.original=Objects.requireNonNull(original);this.gameplay=Objects.requireNonNull(gameplay);this.reconciliation=Objects.requireNonNull(reconciliation);
        this.snapshots=Objects.requireNonNull(snapshots);this.archives=Objects.requireNonNull(archives);this.frames=Objects.requireNonNull(frames);this.results=Objects.requireNonNull(results);
        need(gameplay.operation().equals(kind.resultOperation())&&reconciliation.operation().equals(kind.resultOperation())
                &&gameplay.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP&&reconciliation.guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                &&!gameplay.contractId().equals(reconciliation.contractId()),"two exact independently installed result guard contracts required");
    }
    public NativeRequest prepare(ActionCommand command){need(command.operation().equals(kind.operation()),"wrong conversion family");return original.prepare(command);}
    public static Submission decodeSubmission(Kind kind,ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack) {
        Objects.requireNonNull(kind);Objects.requireNonNull(command);Objects.requireNonNull(attempt);Objects.requireNonNull(ack);
        need(command.operation().equals(kind.operation())&&ack.requestId().equals(attempt.requestId())&&attempt.preparedRequest().step().equals(kind.operation().value()),"original submission operation/request drift");
        need(ack.nativeOk()&&ack.originalResultToken().isPresent(),"native positive owner packet required");
        ObjectNode e;
        try {
            NativeWire.Frame decoded=NativeWire.decode(ack.originalPacket());need(decoded instanceof NativeWire.CommandResult,"original command_result required");var packet=(NativeWire.CommandResult)decoded;
            need(packet.requestId().equals(ack.requestId())&&packet.nativeOk()&&Arrays.equals(packet.payload().value(),ack.originalFrame().bytes()),"complete original native ACK changed");
            ObjectNode full=parse(new RawJson(packet.payload().value()));exact(full,"type protocol_version request_id ok result");e=object(field(full,"result"));need(e.equals(parse(ack.originalResultToken().orElseThrow())),"original result token differs from actual packet");
            var outgoing=ack.outbound().orElseThrow(()->new IllegalArgumentException("original submission lacks actual outbound custody"));ack.custody().orElseThrow(()->new IllegalArgumentException("original submission lacks actual sampling custody")).verify(ack,attempt.guard());
            NativeWire.ExecuteRequest sent=NativeWire.decodeExecuteRequest(outgoing.originalPacket());
            need(sent.requestId().equals(attempt.requestId())&&sent.step().equals(kind.operation().value())&&sent.expectedRevision().equals(Optional.of(command.before().frame().identity().nativeRevision()))
                    &&sent.expectedSnapshotRevision().equals(sent.expectedRevision()),"outbound native/snapshot revision drift");
            ObjectNode fields=parse(new RawJson(sent.normalizedAdditionalFields().value()));fields.put("expected_snapshot_revision",sent.expectedSnapshotRevision().orElseThrow());
            need(fields.equals(parse(attempt.preparedRequest().additionalFields()))&&fields.equals(ReligionCapabilities.argumentNode(command.arguments())),"outbound original command arguments changed");
        }catch(IOException failure){throw new IllegalArgumentException("invalid original conversion native packet",failure);}
        ObjectNode args=ReligionCapabilities.argumentNode(command.arguments());var before=command.before().frame();var id=before.identity();
        equal(e,"step",kind.operation().value());yes(e,"accepted");yes(e,"private_build");no(e,"advertised");no(e,"read_only");equal(e,"backend_id","native-headless");
        PlayerReligionContext.Build build=PlayerReligionContext.Build.exact(text(e,"game_version"),text(e,"executable_sha256"));
        need(!build.version().equals("1.20.0.2")&&(kind==Kind.COUNTY||build.version().equals("1.20.0.3")),"operation requires its actual qualified exact build");
        try{NativeWire.Frame connected=NativeWire.decode(originalPacket(attempt.guard().capabilityEvidence()));need(connected instanceof NativeWire.Hello,"original action guard must retain actual HELLO");var hello=(NativeWire.Hello)connected;
            need(hello.pid()==command.before().game().pid()&&hello.connectionGeneration().equals(attempt.guard().connectionGeneration())&&hello.buildMatch()&&hello.adapterStatus().equals("ready")&&hello.gameSha256().equalsIgnoreCase(build.sha256()),"owner envelope differs from original guarded actual Native build/process/connection");
        }catch(IOException malformed){throw new IllegalArgumentException("original action HELLO malformed",malformed);}
        equal(e,"snapshot_revision",id.nativeRevision());equal(e,"public_revision",before.revision());equal(e,"date_raw",id.dateRaw());BigInteger epoch=number(e,"capture_epoch",BigInteger.ONE,U64);
        ObjectNode owner=object(field(e,"submission"));ObjectNode intended=args.deepCopy();intended.remove(List.of("expected_snapshot_revision","expected_public_revision","expected_date_raw","expected_player_character_id"));intended.put("expected_revision",before.revision());
        need(object(field(owner,"request")).equals(intended),"retained owner differs from complete request");equal(owner,"request_id",attempt.requestId());equal(owner,"native_revision",id.nativeRevision());equal(owner,"date_raw",id.dateRaw());equal(owner,"capture_epoch",epoch);
        equal(args,"expected_snapshot_revision",id.nativeRevision());equal(args,"expected_public_revision",before.revision());equal(args,"expected_date_raw",id.dateRaw());equal(args,"expected_player_character_id",id.player());
        return normalizeSubmission(kind,ReligionCapabilities.raw(e),new ReligionConversionRead.BoundFrame(build,id.dateRaw(),id.player()),before.revision(),id.nativeRevision(),attempt.requestId(),ReligionCapabilities.raw(intended));
    }
    /** Pure original-owner boundary, also used by the original Python differential test. */
    public static Submission normalizeSubmission(Kind kind,RawJson envelope,ReligionConversionRead.BoundFrame frame,BigInteger publicRevision,BigInteger nativeRevision,String requestId,RawJson originalIntent) {
        // Original conversion _frame is a private positive-actor gate; County/public observations retain signed IDs.
        if(kind==Kind.CONVERSION)range(frame.player(),BigInteger.ONE,U32.subtract(BigInteger.ONE));
        ObjectNode e=parse(envelope),owner=object(field(e,"submission"));
        equal(e,"step",kind.operation().value());yes(e,"accepted");yes(e,"private_build");no(e,"advertised");no(e,"read_only");equal(e,"backend_id","native-headless");
        need(PlayerReligionContext.Build.exact(text(e,"game_version"),text(e,"executable_sha256"))==frame.build(),"submission connected build drift");
        need(kind==Kind.COUNTY?!frame.build().version().equals("1.20.0.2"):frame.build().version().equals("1.20.0.3"),"original submission build unsupported");
        equal(e,"public_revision",publicRevision);equal(e,"snapshot_revision",nativeRevision);equal(owner,"native_revision",nativeRevision);equal(e,"date_raw",frame.dateRaw());equal(owner,"request_id",requestId);equal(owner,"date_raw",frame.dateRaw());equal(owner,"capture_epoch",number(e,"capture_epoch",BigInteger.ONE,U64));
        equal(parse(originalIntent),"expected_revision",publicRevision);
        need(object(field(owner,"request")).equals(parse(originalIntent)),"original action intent changed");
        Submission submission=kind==Kind.CONVERSION?new ConversionSubmission(ConversionDecoders.religionOwner(owner,frame.player()),envelope,ReligionCapabilities.raw(owner),frame.build())
                :new CountySubmission(ConversionDecoders.countyOwner(owner,frame.player()),envelope,ReligionCapabilities.raw(owner),frame.build());
        if(submission instanceof ConversionSubmission conversion&&conversion.status()!=SubmitStatus.NOT_SUBMITTED) {
            var baseline=(ReligionConversionRead.Outcome)ReligionConversionRead.normalize(ReligionConversionRead.Kind.OUTCOME,ReligionCapabilities.raw(object(field(owner,"before"))),frame,conversion.owner().request().targetRite().value());
            need(baseline.source().captureEpoch().equals(number(e,"capture_epoch",BigInteger.ONE,U64))&&baseline.actorSource().available()&&baseline.context().available(),"retained before lacks actual available actor/context");
            if(conversion.status()==SubmitStatus.QUEUED_VERIFICATION_PENDING)ReligionConversionRead.normalize(ReligionConversionRead.Kind.TERMS,ReligionCapabilities.raw(object(field(owner,"paid_terms"))),frame,conversion.owner().request().targetRite().value());
        }
        if(submission instanceof CountySubmission county&&county.status()==SubmitStatus.ALREADY_ACTIVE_NOOP)need(countyMatches(county.owner().before(),county.owner()),"county noop lacks preexisting assignment");
        if(submission.status()!=SubmitStatus.QUEUED_VERIFICATION_PENDING)need(!submission.copyCalled(),"cannot declare no-dispatch after submit copy");
        return submission;
    }
    public static boolean countyMatches(TaskState task,CountyOwner owner) {
        return task.available()&&task.ownerId()==owner.playerId()&&Objects.equals(task.incumbent(),owner.request().incumbent().value())
                &&task.activeTask()!=null&&task.activeTask()!=-1&&task.taskKey().equals("task_conversion")&&Objects.equals(task.scopeTag(),8)
                &&Objects.equals(task.province(),owner.request().province().value())&&Objects.equals(task.countyTitle(),owner.targetCounty());
    }
    public static List<ExpectedValue> expected(Kind kind,ObjectNode args) {
        if(kind==Kind.CONVERSION)return List.of(new ExpectedBoolean(new FieldKey("religion.conversion_material"),true),new ExpectedInteger(new FieldKey("religion.target_rite_id"),id(args,"target_rite_id")));
        return List.of(new ExpectedBoolean(new FieldKey("religion.county_assignment_material"),true),new ExpectedInteger(new FieldKey("religion.province_id"),number(args,"province_id",BigInteger.ONE,I32_MAX)));
    }
    private static String noDispatchReason(Submission owner){return "native-owner-no-dispatch:"+owner.kind().name()+":"+owner.status().name();}
    public NativeEffectRegistry.Projected observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
        ActionPorts.OutcomeArchive archive=archives.get();
        if(!(dispatch instanceof NativeActionPort.AckReceived ack))return NativeEffectRegistry.Projected.pending("original conversion owner unresolved; do not repeat submission",List.of(attempt.guard().nativeEvidence()));
        try {
            Submission owner=decodeSubmission(kind,command,attempt,ack);
            if(owner.status()!=SubmitStatus.QUEUED_VERIFICATION_PENDING)return new NativeEffectRegistry.Projected(new ActionPorts.RejectionObserved(new ActionState.Rejected(attempt.requestId(),noDispatchReason(owner),archive.referenceOf(dispatch))),Optional.empty());
            NativeEffectSnapshots.Pair pair=snapshots.read(command,attempt);PlanningReadReceipt read=results.read(command,attempt,pair.after());
            Object decoded=verifiedResult(command,attempt,pair.after(),read,owner,archive);
            if(!material(decoded))return NativeEffectRegistry.Projected.pending("queued conversion awaits independent native material",List.of(archive.readReferenceOf(read),archive.referenceOf(dispatch)));
            RawJson compatible=ReligionCapabilities.raw(resultPresentation(decoded,read));ExactRef basis=NativeEffectEvidence.preserve(command,attempt,pair,List.of(read),compatible,archive);
            return NativeEffectSnapshots.observed(command,attempt,pair.after(),kind.observer(),actual(decoded),read.requestId(),compatible,List.of(basis));
        }catch(IllegalArgumentException|IllegalStateException|java.io.UncheckedIOException unavailable){return NativeEffectRegistry.Projected.pending("original conversion evidence unavailable; retain UNKNOWN: "+unavailable.getMessage(),List.of(archive.referenceOf(dispatch),attempt.guard().nativeEvidence()));}
    }
    private Object verifiedResult(ActionCommand command,ActionState.Attempt attempt,Complete after,PlanningReadReceipt read,Submission originalOwner,ActionPorts.OutcomeArchive archive) {
        NativeRecordedEvidenceVerifier.requireRead(read,archive);ReligionService.requireGuards(read);ObjectNode envelope=ReligionService.originalResult(read);
        NativeEffectSnapshots.requireAfterRead(command,attempt,after,read,kind.resultOperation());
        ReadContract<?> contract=read.request().origin() instanceof CommandOrigin.Reconciliation?reconciliation:gameplay;
        need(read.contractId().equals(contract.contractId()),"result must use identical installed original contract");Object decoded=contract.replay(read);
        need(parse(originalOwner.originalOwner()).equals(object(field(envelope,"submission"))),"independent result changed the complete owning baseline");
        if(kind==Kind.CONVERSION)need(decoded instanceof ConversionResult,"wrong conversion result decoder");else need(decoded instanceof CountyResult,"wrong county result decoder");return decoded;
    }
    private static boolean material(Object decoded){return decoded instanceof ConversionResult c?c.materialObserved():((CountyResult)decoded).materialObserved();}
    private static List<ExpectedValue> actual(Object decoded) {
        if(decoded instanceof ConversionResult value)return List.of(new ExpectedBoolean(new FieldKey("religion.conversion_material"),value.materialObserved()),new ExpectedInteger(new FieldKey("religion.target_rite_id"),value.after().actor().religion().riteId()));
        CountyResult value=(CountyResult)decoded;return List.of(new ExpectedBoolean(new FieldKey("religion.county_assignment_material"),value.materialObserved()),new ExpectedInteger(new FieldKey("religion.province_id"),BigInteger.valueOf(value.after().province())));
    }
    private static ObjectNode resultPresentation(Object value,PlanningReadReceipt read) {
        var build=ReligionService.boundBuild(read);ObjectNode envelope=ReligionService.originalResult(read);
        return value instanceof ConversionResult conversion?ReligionService.presentConversion(conversion,build,envelope):ReligionService.presentCounty((CountyResult)value,build,envelope);
    }
    public NativeRecordedEvidenceVerifier.Binding archived(ExactRef producer) {
        return new NativeRecordedEvidenceVerifier.Binding(kind.operation(),producer,(head,receipt,archive)->{
            need(receipt.state() instanceof ActionState.Settled,"conversion settlement must retain primitive attempt");var settled=(ActionState.Settled)receipt.state();
            need(settled.dispatch() instanceof NativeActionPort.AckReceived,"settlement lacks original owner packet");Submission owner=decodeSubmission(kind,receipt.command(),settled.attempt(),(NativeActionPort.AckReceived)settled.dispatch());
            if(settled.settlement() instanceof ActionState.Rejected rejected){need(owner.status()!=SubmitStatus.QUEUED_VERIFICATION_PENDING&&!owner.copyCalled()&&rejected.reason().equals(noDispatchReason(owner))&&rejected.originalEvidence().equals(archive.referenceOf(settled.dispatch())),"native no-dispatch proof changed");return;}
            need(settled.settlement() instanceof ActionState.Applied,"conversion cannot borrow another settlement plane");var basis=NativeEffectEvidence.load(receipt,archive,frames);need(basis.independentReads().size()==1,"exact one independent result required");var read=basis.independentReads().getFirst();
            Object result=verifiedResult(receipt.command(),settled.attempt(),basis.frames().after(),read,owner,archive);need(owner.status()==SubmitStatus.QUEUED_VERIFICATION_PENDING&&material(result),"archived owner/result lacks real material");
            var effect=((ActionState.Applied)settled.settlement()).observation();need(effect.observerSchema().equals(kind.observer())&&effect.actual().equals(actual(result))&&effect.after().equals(basis.frames().after().identity())&&effect.provenance().equals(new ObservationProvenance.Query(read.requestId())),"archived effect differs from original native facts");
            need(parse(basis.compatibleResult()).equals(resultPresentation(result,read)),"archived public result differs from original replay");
        });
    }
    /** Original submission response, with explicit fixed-width decimal roles at the public boundary. */
    public static ObjectNode presentSubmission(Submission value) {
        ObjectNode owner=parse(value.originalOwner());ObjectNode n=ReligionCapabilities.empty().put("schema",value.kind()==Kind.CONVERSION?"xar.ck3.player-religion-conversion-private-action.v1":"xar.ck3.county-conversion-task-private-action.v1")
                .put("exact_ck3_build",value.build().version()).put("exe_sha256",value.build().sha256()).put("request_id",value.requestId()).put("action_id",value.actionId()).put("material_result",false).put("automatic_retry",false).put("advertised",false);
        boolean queued=value.status()==SubmitStatus.QUEUED_VERIFICATION_PENDING;
        if(value instanceof ConversionSubmission v) {
            var o=v.owner();n.put("player_character_id",o.playerId()).put("target_rite_id",o.request().targetRite().value()).put("pay_piety",true).put("max_piety_cost_raw",o.request().maximumPiety().toString())
                    .put("submitted",queued).put("verification_pending",queued).put("raw_scale",100000).putNull("before_outcome").putNull("paid_terms").putNull("quoted_base_piety_cost_raw");
            n.set("native_reasons",owner.has("native_reasons")?owner.get("native_reasons").deepCopy():com.fasterxml.jackson.databind.node.NullNode.instance);if(n.get("native_reasons") instanceof ObjectNode reasons)decimal(reasons,"capture_epoch");
            n.put("status",queued?"submitted_verification_pending":o.status()==SubmitStatus.ALREADY_TARGET_NOOP?"noop_preexisting_target_match":"rejected_before_submit");
            if(o.status()==SubmitStatus.NOT_SUBMITTED)n.set("failure",owner.has("failure")?owner.get("failure").deepCopy():com.fasterxml.jackson.databind.node.NullNode.instance);
            else {
                var frame=new ReligionConversionRead.BoundFrame(value.build(),BigInteger.valueOf(o.dateRaw()),o.playerId());
                n.set("before_outcome",ReligionConversionRead.publicData(ReligionConversionRead.normalize(ReligionConversionRead.Kind.OUTCOME,ReligionCapabilities.raw(object(owner.get("before"))),frame,o.request().targetRite().value())));
                if(queued){n.set("paid_terms",ReligionConversionRead.publicData(ReligionConversionRead.normalize(ReligionConversionRead.Kind.TERMS,ReligionCapabilities.raw(object(owner.get("paid_terms"))),frame,o.request().targetRite().value())));n.put("quoted_base_piety_cost_raw",o.paidTerms().pietyCost().toString());}
            }
        }else {
            var o=((CountySubmission)value).owner();n.put("status",text(owner,"status")).put("failure",o.failure()).put("player_character_id",o.playerId()).put("province_id",o.request().province().value());
            if(o.targetCounty()==null)n.putNull("target_county_title_id");else n.put("target_county_title_id",o.targetCounty());n.put("submitted",queued).put("verification_pending",queued).put("task_assignment_material_observed",false).put("county_conversion_completed",false);
            ObjectNode before=object(owner.get("before")).deepCopy();projectTask(before);n.set("before_task",before);
        }
        projectOwner(owner,value.kind());n.set("owner_submission",owner);return n;
    }
    /** Same original-result presenter calls these finite roles, avoiding independent JSON64 algorithms. */
    public static ObjectNode projectConversionResult(ConversionResult value,ObjectNode originalPublic) {
        ObjectNode n=originalPublic.deepCopy();projectOwner(object(n.get("owner_submission")),Kind.CONVERSION);
        if(value.owner().status()==SubmitStatus.QUEUED_VERIFICATION_PENDING) {
            for(String field:List.of("piety_net_delta_raw","gold_net_delta_raw","prestige_net_delta_raw"))wideDecimal(n,field);decimal(n,"quoted_base_piety_cost_raw");
            for(String field:List.of("piety_raw","gold_raw","prestige_raw"))wideDecimal(object(n.get("actual_net_resources_raw")),field);
            for(String field:List.of("before_outcome","after_outcome"))projectOutcome(object(n.get(field)));
            ObjectNode result=object(n.get("owner_result"));projectOutcome(object(result.get("after")));
            for(String field:List.of("piety_net_delta_raw","gold_net_delta_raw","prestige_net_delta_raw"))wideDecimal(result,field);decimal(result,"quoted_base_piety_cost_raw");
        }
        return n;
    }
    public static ObjectNode projectCountyResult(CountyResult value,ObjectNode originalPublic) {
        Objects.requireNonNull(value);ObjectNode n=originalPublic.deepCopy();projectOwner(object(n.get("owner_submission")),Kind.COUNTY);
        projectTask(object(n.get("before_task")));projectTask(object(n.get("after_task")));projectTask(object(object(n.get("owner_result")).get("after")));return n;
    }
    private static void wideDecimal(ObjectNode n,String field){decimal(n,field,I64_MIN.subtract(I64_MAX),I64_MAX.subtract(I64_MIN));}
    private static void decimal(ObjectNode n,String field){boolean unsigned=SetNames.UNSIGNED.contains(field);decimal(n,field,unsigned?BigInteger.ZERO:I64_MIN,unsigned?U64:I64_MAX);}
    private static final class SetNames {private static final java.util.Set<String> UNSIGNED=java.util.Set.of("capture_epoch","native_revision","expected_revision","max_piety_cost_raw");}
    private static void decimal(ObjectNode n,String field,BigInteger low,BigInteger high){JsonNode value=n.get(field);need(value!=null,"missing original decimal role: "+field);if(!value.isNull()){
        BigInteger exact;if(value.isTextual()){need(value.textValue().matches("0|-?[1-9][0-9]*"),"noncanonical decimal role");exact=new BigInteger(value.textValue());}
        else {need(value.isIntegralNumber(),"original decimal role not integral: "+field);exact=value.bigIntegerValue();}range(exact,low,high);n.put(field,exact.toString());}}
    private static void projectTask(ObjectNode n){decimal(n,"capture_epoch");decimal(n,"percentage_progress_raw");}
    private static void projectOwner(ObjectNode owner,Kind kind) {
        decimal(owner,"native_revision");decimal(owner,"capture_epoch");decimal(object(owner.get("request")),"expected_revision");
        if(kind==Kind.COUNTY){projectTask(object(owner.get("before")));return;}
        decimal(object(owner.get("request")),"max_piety_cost_raw");if(owner.get("native_reasons") instanceof ObjectNode reasons)decimal(reasons,"capture_epoch");
        if(owner.hasNonNull("before"))projectOutcome(object(owner.get("before")));
        if(owner.hasNonNull("paid_terms"))projectTerms(object(owner.get("paid_terms")));
    }
    private static void projectTerms(ObjectNode n){decimal(n,"capture_epoch");decimal(object(n.get("final_gate")),"capture_epoch");ObjectNode cost=object(n.get("cost"));for(String field:List.of("capture_epoch","piety_cost_raw","actor_piety_raw"))decimal(cost,field);}
    private static void projectOutcome(ObjectNode n){
        decimal(n,"capture_epoch");ObjectNode actor=object(n.get("actor")),state=object(n.get("state")),religion=object(actor.get("current_religion"));
        for(String field:List.of("capture_epoch","piety_raw","gold_raw","prestige_raw"))decimal(actor,field);
        for(String field:List.of("capture_epoch","faith_fervor_raw","spiritual_fulfillment_raw"))decimal(religion,field);
        for(String field:List.of("capture_epoch","knowledge_level_raw","spiritual_fulfillment_raw","baseline_spiritual_fulfillment_raw"))decimal(state,field);
        for(String field:List.of("faith_conversion_recently_converted","conversion_memory_recently_created","recent_convert"))decimal(object(state.get(field)),"remaining_updates");
    }
}
