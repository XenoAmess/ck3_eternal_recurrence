package org.xar.ck3.control.nativebridge.capabilities.china_cases;

import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Function;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesModel.*;
import static org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.*;

/** Public ZhongGuo API. Install contracts in the one PlanningReadCoordinator; mutations use the existing ActionCoordinator. */
public final class ChinaCasesFacade {
    /** The finite original Cases10 driver branches; archive replay never issues this live diagnostic. */
    public static final class OriginalDriverFailure extends IllegalArgumentException implements OriginalReadDecodeFailure {
        private static final long serialVersionUID=1L;
        public enum Kind {
            B1_MALFORMED_ENVELOPE(Family.B1,"native ZhongGuo B1-cycle query returned a malformed envelope"),
            B1_QUERY_SEQUENCE_MISSING(Family.B1,"native ZhongGuo B1-cycle query lacks a query sequence"),
            CASE_MALFORMED_ENVELOPE(Family.CASE,"native ZhongGuo case query returned a malformed envelope"),
            CASE_QUERY_SEQUENCE_MISSING(Family.CASE,"native ZhongGuo case query lacks query_sequence"),
            AIOWNED_MALFORMED_ENVELOPE(Family.AIOWNED,"native ZhongGuo AI-owned case query returned a malformed envelope"),
            AIOWNED_QUERY_SEQUENCE_MISSING(Family.AIOWNED,"native ZhongGuo AI-owned case query lacks query_sequence"),
            RESULT_MALFORMED_ENVELOPE(Family.RESULT,"native ZhongGuo result-case query returned a malformed envelope"),
            RESULT_QUERY_SEQUENCE_MISSING(Family.RESULT,"native ZhongGuo result-case query lacks query_sequence"),
            PIP_MALFORMED_ENVELOPE(Family.PIP,"native ZhongGuo B2 PIP query returned a malformed envelope"),
            PIP_QUERY_SEQUENCE_MISSING(Family.PIP,"native ZhongGuo B2 PIP query lacks query_sequence"),
            PROMOTION_MALFORMED_ENVELOPE(Family.PROMOTION,"native ZhongGuo promotion/compensation query returned a malformed envelope"),
            PROMOTION_QUERY_SEQUENCE_MISSING(Family.PROMOTION,"native ZhongGuo promotion/compensation query lacks query_sequence"),
            AF5_MALFORMED_ENVELOPE(Family.AF5,"native ZhongGuo compensation AF5 query returned a malformed envelope"),
            AF5_QUERY_SEQUENCE_MISSING(Family.AF5,"native ZhongGuo compensation AF5 query lacks query_sequence"),
            PROJECTS_MALFORMED_ENVELOPE(Family.PROJECTS,"native ZhongGuo projects/metrics query returned a malformed envelope"),
            PROJECTS_QUERY_SEQUENCE_MISSING(Family.PROJECTS,"native ZhongGuo projects/metrics query lacks query_sequence"),
            INCIDENT_MALFORMED_ENVELOPE(Family.INCIDENT,"native ZhongGuo incident query returned a malformed envelope"),
            INCIDENT_QUERY_SEQUENCE_MISSING(Family.INCIDENT,"native ZhongGuo incident query lacks query_sequence"),
            SCOREBOARD_MALFORMED_ENVELOPE(Family.SCOREBOARD,"native ZhongGuo scoreboard query returned a malformed envelope"),
            SCOREBOARD_QUERY_SEQUENCE_MISSING(Family.SCOREBOARD,"native ZhongGuo scoreboard query lacks query_sequence"),
            B1_NORMALIZER_REJECTED(Family.B1,"native ZhongGuo B1-cycle contract rejected the frame",true),
            CASE_NORMALIZER_REJECTED(Family.CASE,"native ZhongGuo case query returned a malformed frame: ",true),
            AIOWNED_NORMALIZER_REJECTED(Family.AIOWNED,"native ZhongGuo AI-owned case query returned a malformed frame: ",true),
            RESULT_NORMALIZER_REJECTED(Family.RESULT,"native ZhongGuo result-case query returned a malformed frame: ",true),
            PIP_NORMALIZER_REJECTED(Family.PIP,"native ZhongGuo B2 PIP query returned a malformed frame: ",true),
            PROMOTION_NORMALIZER_REJECTED(Family.PROMOTION,"native ZhongGuo promotion/compensation frame is malformed: ",true),
            AF5_NORMALIZER_REJECTED(Family.AF5,"native ZhongGuo compensation AF5 frame is malformed: ",true),
            PROJECTS_NORMALIZER_REJECTED(Family.PROJECTS,"native ZhongGuo projects/metrics frame is malformed: ",true),
            INCIDENT_NORMALIZER_REJECTED(Family.INCIDENT,"native ZhongGuo incident query returned a malformed frame: ",true),
            SCOREBOARD_NORMALIZER_REJECTED(Family.SCOREBOARD,"native ZhongGuo scoreboard query returned a malformed frame: ",true);
            private final Family family;
            private final String originalMessage;
            private final boolean normalizer;
            Kind(Family family,String message){this(family,message,false);}
            Kind(Family family,String message,boolean normalizer){this.family=family;originalMessage=message;this.normalizer=normalizer;}
            public boolean normalizer(){return normalizer;}
            public Family family(){return family;}
        }
        private final transient ChinaCasesFacade producer;
        private final transient ReadContract<?> contract;
        private final transient PlanningReadRequest request;
        private final transient PlanningReadReceipt receipt;
        private final Kind kind;
        private final String exactOriginalMessage;
        private OriginalDriverFailure(ChinaCasesFacade actualProducer,ReadContract<?> identicalInstalled,
                PlanningReadReceipt actualReceipt,Kind actualBranch) {
            this(actualProducer,identicalInstalled,actualReceipt,actualBranch,null);
        }
        private OriginalDriverFailure(ChinaCasesFacade actualProducer,ReadContract<?> identicalInstalled,
                PlanningReadReceipt actualReceipt,Kind actualBranch,
                ChinaCasesOriginalNormalizers.NormalizationFailure original) {
            super(actualBranch.originalMessage+(original!=null&&actualBranch.family()!=Family.B1?original.getMessage():""),original);
            StrictJson.require(actualBranch.normalizer==(original!=null),"original normalizer cause and branch differ");
            if(original!=null)StrictJson.require(original.family()==actualBranch.family(),"normalizer failure crossed its family");
            exactOriginalMessage=getMessage();
            producer=Objects.requireNonNull(actualProducer);contract=Objects.requireNonNull(identicalInstalled);
            receipt=Objects.requireNonNull(actualReceipt);request=receipt.request();kind=Objects.requireNonNull(actualBranch);
            requireProducer(producer,contract,request);
        }
        public Kind kind(){return kind;}
        public String originalErrorClass(){return "BridgeUnavailableError";}
        public String originalMessage(){return exactOriginalMessage;}
        @Override public void requireOriginal(ReadContract<?> identicalInstalled,PlanningReadRequest actualRequest,
                PlanningReadReceipt actualReceipt) {
            StrictJson.require(contract==Objects.requireNonNull(identicalInstalled)
                    &&request==Objects.requireNonNull(actualRequest)&&receipt==Objects.requireNonNull(actualReceipt),
                    "Cases10 original decode failure crossed its identical installed contract, request or receipt");
            requireProducer(producer,identicalInstalled,actualRequest);
        }
        public void requireProducer(ChinaCasesFacade identicalFacade,ReadContract<?> identicalInstalled,
                PlanningReadRequest actualRequest) {
            StrictJson.require(producer==Objects.requireNonNull(identicalFacade)&&contract==identicalInstalled
                    &&request==actualRequest&&producer.originalFailureContract(kind.family())==contract
                    &&receipt.contractId().equals(contract.contractId())
                    &&request.operation().equals(contract.operation())
                    &&contract.sourceRef().equals(ChinaCasesSources.contract(kind.family())),
                    "Cases10 original driver failure does not belong to this exact source-installed producer");
        }
    }
    public record Context(ObservationIdentity before,G2Source source,String sessionId,BigInteger connectionGeneration,Instant deadline) {
        public Context {
            Objects.requireNonNull(before); Objects.requireNonNull(source); StrictJson.text(sessionId); Objects.requireNonNull(deadline);
            StrictJson.require(connectionGeneration!=null && connectionGeneration.signum()>0 && connectionGeneration.compareTo(StrictJson.UINT64_MAX)<=0,"positive uint64 generation");
            StrictJson.require(before.machineId().equals(source.machineId()),"context machine drift");
        }
        PlanningReadRequest request(Family f,ObjectNode fields) {
            return new PlanningReadRequest(before,source,sessionId,new OperationKey(f.step()),
                    (OpportunityJson.Obj)OpportunityJson.parse(StrictJson.canonical(fields)),deadline);
        }
    }
    public enum CaseKind { B1_PERFORMANCE }
    public enum SurfaceId { MANAGED_CAPABLE, RECEIVED_ONLY }
    public sealed interface SurfaceResult permits SurfaceReady,SurfaceUnavailable { SurfaceId surface(); }
    /** Lifecycle/checkpoint owner supplies real restart evidence and the independent restored scoreboard query. */
    public record SurfaceReady(SurfaceId surface,ExactRef originalProviderReceipt,ExactRef checkpoint,PlanningReadResult.Known<ScoreboardFrame> postRestoreQuery) implements SurfaceResult {
        public SurfaceReady {
            Objects.requireNonNull(surface); Objects.requireNonNull(originalProviderReceipt); Objects.requireNonNull(checkpoint); Objects.requireNonNull(postRestoreQuery);
            StrictJson.require(originalProviderReceipt.bytes()>0 && checkpoint.bytes()>0,"real checkpoint/provider evidence required");
            var s=postRestoreQuery.value(); StrictJson.require(s.header().status()==Status.AVAILABLE,"restored scoreboard unavailable");
            StrictJson.require(surface==SurfaceId.MANAGED_CAPABLE?s.acl().managed().surfaceAvailable():
                s.acl().receivedSelf().surfaceAvailable() && !s.acl().managed().surfaceAvailable(),"restored surface ACL differs");
        }
    }
    public record SurfaceUnavailable(SurfaceId surface,String reason) implements SurfaceResult {
        public SurfaceUnavailable { Objects.requireNonNull(surface); StrictJson.text(reason); }
    }
    @FunctionalInterface public interface SurfacePreparer { SurfaceResult prepare(SurfaceId surface); }
    private final AtomicReference<SurfacePreparer> surfacePreparer=new AtomicReference<>();
    private final PlanningReadPort reads;
    private final ActionCoordinatorPort actions;
    private final ReadContract<B1Frame> b1;
    private final ReadContract<CaseFrame> cases;
    private final ReadContract<AiOwnedFrame> ai;
    private final ReadContract<ResultFrame> result;
    private final ReadContract<PipFrame> pip;
    private final ReadContract<PromotionFrame> promotion;
    private final ReadContract<Af5Frame> af5;
    private final ReadContract<ProjectsFrame> projects;
    private final ReadContract<IncidentFrame> incident;
    private final ReadContract<ScoreboardFrame> scoreboard;
    private final ReadContract<ProgressFrame> progress;
    /** Source-owned original-history projection only; no replacement decoder/permission callback. */
    public interface HistoryProjectionFactory {
        org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.Kind kind();
        <T> Optional<ReadContract.OriginalHistoryProjection<T>> forFamily(Family family);
    }
    public ChinaCasesFacade(PlanningReadPort reads,ActionCoordinatorPort actions) {
        this(reads,actions,Optional.empty());
    }
    /** Formal Root must pass its actual source-bound Cases10 history factory before catalog installation. */
    public ChinaCasesFacade(PlanningReadPort reads,ActionCoordinatorPort actions,HistoryProjectionFactory actual) {
        this(reads,actions,Optional.of(Objects.requireNonNull(actual)));
    }
    private ChinaCasesFacade(PlanningReadPort reads,ActionCoordinatorPort actions,Optional<HistoryProjectionFactory> actual) {
        this.reads=Objects.requireNonNull(reads);this.actions=Objects.requireNonNull(actions);
        b1=configured(actual,Family.B1,ChinaCasesCodec::decodeB1Frame);
        cases=configured(actual,Family.CASE,ChinaCasesCodec::decodeCaseFrame);
        ai=configured(actual,Family.AIOWNED,ChinaCasesCodec::decodeAiOwnedFrame);
        result=configured(actual,Family.RESULT,ChinaCasesCodec::decodeResultFrame);
        pip=configured(actual,Family.PIP,ChinaCasesCodec::decodePipFrame);
        promotion=configured(actual,Family.PROMOTION,ChinaCasesCodec::decodePromotionFrame);
        af5=configured(actual,Family.AF5,ChinaCasesCodec::decodeAf5Frame);
        projects=configured(actual,Family.PROJECTS,ChinaCasesCodec::decodeProjectsFrame);
        incident=configured(actual,Family.INCIDENT,ChinaCasesCodec::decodeIncidentFrame);
        scoreboard=configured(actual,Family.SCOREBOARD,ChinaCasesCodec::decodeScoreboardFrame);
        progress=configured(actual,Family.PROGRESS,ChinaCasesCodec::decodeProgressFrame);
    }
    private <T> ReadContract<T> configured(Optional<HistoryProjectionFactory> actual,Family family,Function<PlanningReadReceipt,T> decoder) {
        ReadContract<T> original=contract(family,decoder);
        if(actual.isEmpty())return original; // The pre-existing two-argument nonformal API is explicit.
        HistoryProjectionFactory factory=actual.orElseThrow();
        Optional<ReadContract.OriginalHistoryProjection<T>> projection=Objects.requireNonNull(factory.<T>forFamily(family));
        StrictJson.require((family!=Family.PROGRESS)==projection.isPresent(),
            "formal Cases10 projector required exactly for ten families; PROGRESS is outside this EXECUTE registry");
        return projection.isEmpty()?original:original.withOriginalHistoryProjection(
            Objects.requireNonNull(factory.kind()),projection.orElseThrow());
    }
    public List<ReadContract<?>> readContracts() { return List.of(b1,cases,ai,result,pip,promotion,af5,projects,incident,scoreboard,progress); }
    /** Direct service consumption retains the private live cause and its actual request; it creates no new receipt. */
    public void requireDirectOriginalFailure(OriginalDriverFailure actualFault,Family family,Context actualContext) {
        Objects.requireNonNull(actualFault);Objects.requireNonNull(family);Objects.requireNonNull(actualContext);
        StrictJson.require(family==actualFault.kind().family(),"original Cases failure crossed its actual family");
        actualFault.requireProducer(this,originalFailureContract(family),actualFault.request);
        var request=actualFault.request;
        StrictJson.require(request.before().equals(actualContext.before())&&request.source().equals(actualContext.source())
                &&request.sessionId().equals(actualContext.sessionId())&&request.operation().equals(originalFailureContract(family).operation())
                &&request.deadline().equals(actualContext.deadline())
                &&actualFault.receipt.before().binding().connectionGeneration().equals(actualContext.connectionGeneration())
                &&actualFault.receipt.after().binding().connectionGeneration().equals(actualContext.connectionGeneration()),
                "direct original Cases10 failure crossed the actual source, frame, session or connection generation");
    }
    private ReadContract<?> originalFailureContract(Family family) {
        return switch(family) {
            case B1 -> b1;
            case CASE -> cases;
            case AIOWNED -> ai;
            case RESULT -> result;
            case PIP -> pip;
            case PROMOTION -> promotion;
            case AF5 -> af5;
            case PROJECTS -> projects;
            case INCIDENT -> incident;
            case SCOREBOARD -> scoreboard;
            case PROGRESS -> throw new IllegalArgumentException("PROGRESS has no Cases10 original driver branch");
        };
    }
    private <T> ReadContract<T> contract(Family f,Function<PlanningReadReceipt,T> decoder) {
        return new ReadContract<>("china-cases/"+f.step()+"/v1",new OperationKey(f.step()),Optional.of(f.capability()),
            "original-native/"+f.step(),ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,
            ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,ChinaCasesSources.contract(f),
            (request,requestId)->{ChinaCasesSources.verify(f); validateArguments(f,request.arguments()); return new NativeRequest(f.step(),f.capability(),new RawJson(OpportunityJson.encode(request.arguments())));},
            receipt->{
                ChinaCasesSources.verify(f);
                if(f!=Family.PROGRESS)ChinaCasesCodec.originalDriverEnvelopeFailure(receipt,f).ifPresent(branch->{
                    // configured() can return a decorated immutable contract. Resolve the actual final
                    // field only when the installed live decoder runs, after construction is complete.
                    throw new OriginalDriverFailure(this,Objects.requireNonNull(originalFailureContract(f)),receipt,branch);
                });
                if(f!=Family.PROGRESS)try {
                    ChinaCasesOriginalNormalizers.normalize(receipt,f);
                } catch(ChinaCasesOriginalNormalizers.NormalizationFailure original) {
                    throw new OriginalDriverFailure(this,Objects.requireNonNull(originalFailureContract(f)),receipt,
                            normalizerFailureKind(f),original);
                }
                return decoder.apply(receipt);
            },
            receipt->{ChinaCasesSources.verify(f); return decoder.apply(receipt);});
    }
    private static OriginalDriverFailure.Kind normalizerFailureKind(Family family) {
        return switch(family) {
            case B1 -> OriginalDriverFailure.Kind.B1_NORMALIZER_REJECTED;
            case CASE -> OriginalDriverFailure.Kind.CASE_NORMALIZER_REJECTED;
            case AIOWNED -> OriginalDriverFailure.Kind.AIOWNED_NORMALIZER_REJECTED;
            case RESULT -> OriginalDriverFailure.Kind.RESULT_NORMALIZER_REJECTED;
            case PIP -> OriginalDriverFailure.Kind.PIP_NORMALIZER_REJECTED;
            case PROMOTION -> OriginalDriverFailure.Kind.PROMOTION_NORMALIZER_REJECTED;
            case AF5 -> OriginalDriverFailure.Kind.AF5_NORMALIZER_REJECTED;
            case PROJECTS -> OriginalDriverFailure.Kind.PROJECTS_NORMALIZER_REJECTED;
            case INCIDENT -> OriginalDriverFailure.Kind.INCIDENT_NORMALIZER_REJECTED;
            case SCOREBOARD -> OriginalDriverFailure.Kind.SCOREBOARD_NORMALIZER_REJECTED;
            case PROGRESS -> throw new IllegalArgumentException("PROGRESS has no Cases10 normalizer");
        };
    }
    static void validateArguments(Family f,OpportunityJson.Obj args) {
        ObjectNode n=(ObjectNode)OpportunityJson.toNode(args);
        Set<String> keys=switch(f) {
            case B1 -> Set.of("request_nonce");
            case CASE -> Set.of("request_nonce","case_kind","subject_character_id","owner_character_id");
            case AIOWNED -> Set.of("request_nonce","subject_character_id","owner_character_id");
            case RESULT,PIP,INCIDENT,PROMOTION,AF5,PROGRESS -> f==Family.INCIDENT?Set.of("request_nonce","owner_character_id","profile"):Set.of("request_nonce","owner_character_id");
            case PROJECTS -> Set.of("request_nonce","owner_character_id","subject_character_id");
            case SCOREBOARD -> Set.of("request_nonce","expected_connection_generation");
        };
        exact(n,keys); new Nonce(text(n.get("request_nonce")));
        if(n.has("owner_character_id")) {
            BigInteger id=integer(n.get("owner_character_id"));
            boolean wide=f==Family.PROMOTION||f==Family.AF5||f==Family.PROJECTS;
            check(id.toString().length()<=4300&&id.signum()>=0&&(wide||id.compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0),"owner original integer domain");
            if(f!=Family.CASE)check(id.signum()>0,"explicit owner required");
        }
        if(n.has("subject_character_id")) {
            if(f==Family.PROJECTS) {
                BigInteger subject=integer(n.get("subject_character_id"));
                check(subject.signum()>0&&subject.toString().length()<=4300,"project subject original positive integer domain");
            } else character(n.get("subject_character_id"));
        }
        if(f==Family.AIOWNED||f==Family.PROJECTS)check(!integer(n.get("owner_character_id")).equals(integer(n.get("subject_character_id"))),"owner and subject must differ");
        if(n.has("case_kind"))check(text(n.get("case_kind")).equals("zhongguo.b1.performance"),"case kind not allowlisted");
        if(n.has("profile"))enumeration(n.get("profile"),IncidentProfile.class);
        if(n.has("expected_connection_generation"))uint64(n.get("expected_connection_generation"),true);
    }
    private static ObjectNode fields(Nonce nonce) { ObjectNode n=StrictJson.object(); n.put("request_nonce",nonce.value()); return n; }
    private static ObjectNode owner(Nonce nonce,CharacterId owner) { ObjectNode n=fields(nonce); n.put("owner_character_id",owner.value()); return n; }
    public void bind_zhongguo_scoreboard_surface_preparer_v1(SurfacePreparer preparer) {
        StrictJson.require(surfacePreparer.compareAndSet(null,Objects.requireNonNull(preparer)),"scoreboard surface preparer already bound");
    }
    public SurfaceResult prepare_zhongguo_scoreboard_surface_v1(SurfaceId surface) {
        Objects.requireNonNull(surface); SurfacePreparer p=surfacePreparer.get();
        if(p==null)return new SurfaceUnavailable(surface,"scoreboard_surface_checkpoint_registry_missing");
        SurfaceResult result=Objects.requireNonNull(p.prepare(surface)); StrictJson.require(result.surface()==surface,"provider returned another surface"); return result;
    }
    public PlanningReadResult<B1Frame> query_zhongguo_b1_cycle_snapshot_v1(Context c,Nonce nonce) { return reads.read(b1,c.request(Family.B1,fields(nonce))); }
    public PlanningReadResult<CaseFrame> query_zhongguo_case_snapshot_v1(Context c,CaseKind kind,Nonce nonce,Optional<CharacterId> subject,Optional<CharacterId> owner) {
        Objects.requireNonNull(kind); ObjectNode n=fields(nonce); n.put("case_kind","zhongguo.b1.performance");
        n.put("subject_character_id",subject.orElseGet(()->new CharacterId(c.before().frame().identity().player().intValueExact())).value());
        n.put("owner_character_id",owner.map(CharacterId::value).orElse(0)); return reads.read(cases,c.request(Family.CASE,n));
    }
    public PlanningReadResult<AiOwnedFrame> query_zhongguo_ai_owned_case_snapshot_v1(Context c,CharacterId owner,CharacterId subject,Nonce nonce) {
        ObjectNode n=owner(nonce,owner); n.put("subject_character_id",subject.value()); return reads.read(ai,c.request(Family.AIOWNED,n));
    }
    public PlanningReadResult<ResultFrame> query_zhongguo_result_case_snapshot_v1(Context c,CharacterId owner,Nonce nonce) { return reads.read(result,c.request(Family.RESULT,owner(nonce,owner))); }
    public PlanningReadResult<PipFrame> query_zhongguo_b2_pip_snapshot_v1(Context c,CharacterId owner,Nonce nonce) { return reads.read(pip,c.request(Family.PIP,owner(nonce,owner))); }
    public PlanningReadResult<PromotionFrame> query_zhongguo_promotion_compensation_postcondition_v1(Context c,Nonce nonce) { return reads.read(promotion,c.request(Family.PROMOTION,owner(nonce,new CharacterId(c.before().frame().identity().player().intValueExact())))); }
    public PlanningReadResult<Af5Frame> query_zhongguo_compensation_af5_snapshot_v1(Context c,Nonce nonce) { return reads.read(af5,c.request(Family.AF5,owner(nonce,new CharacterId(c.before().frame().identity().player().intValueExact())))); }
    public PlanningReadResult<ProjectsFrame> query_zhongguo_projects_metrics_postcondition_v1(Context c,CharacterId owner,Optional<CharacterId> subject,Nonce nonce) {
        ObjectNode n=owner(nonce,owner); n.put("subject_character_id",subject.orElseGet(()->new CharacterId(c.before().frame().identity().player().intValueExact())).value());
        return reads.read(projects,c.request(Family.PROJECTS,n));
    }
    public PlanningReadResult<IncidentFrame> query_zhongguo_incident_snapshot_v1(Context c,CharacterId owner,IncidentProfile profile,Nonce nonce) {
        ObjectNode n=owner(nonce,owner); n.put("profile",profile.name().toLowerCase(java.util.Locale.ROOT)); return reads.read(incident,c.request(Family.INCIDENT,n));
    }
    public PlanningReadResult<ScoreboardFrame> query_zhongguo_scoreboard_state_v1(Context c,Nonce nonce) {
        ObjectNode n=fields(nonce); n.put("expected_connection_generation",c.connectionGeneration()); return reads.read(scoreboard,c.request(Family.SCOREBOARD,n));
    }
    public PlanningReadResult<ProgressFrame> query_zhongguo_promotion_source_progress_v1(Context c,Nonce nonce) { return reads.read(progress,c.request(Family.PROGRESS,owner(nonce,new CharacterId(c.before().frame().identity().player().intValueExact())))); }
    public ActionReceipt activate_zhongguo_review_now_v1(ActionCommand command,PlanningReadResult.Known<ProgressFrame> source) {
        ChinaCasesActions.validateReview(command,source); return actions.execute(command);
    }
    public ActionReceipt activate_zhongguo_scoreboard_v1(ActionCommand command,PlanningReadResult.Known<ScoreboardFrame> source) {
        ChinaCasesActions.validateScoreboard(command,source); return actions.execute(command);
    }
}
