package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJson;

/** Fixed original read operations. The one composition root installs these exact contract instances. */
public final class FinanceReadContracts {
    public static final String ROOT_CONTRACT_ID="ordinary-finance-read:ROOT/v2";
    public static final String MERCENARY_EMPLOYER_CONTRACT_ID="ordinary-finance-read:MERCENARY_EMPLOYER/v1";
    public enum RootCapture { PUBLIC_QUERY, INTERNAL_PRECLOCK_ORIGINALS }
    public static Obj rootArguments(RootCapture capture) {
        return new Obj(java.util.Map.of("capture_context",new Text(Objects.requireNonNull(capture).name()),"public_arguments",new Obj(java.util.Map.of())));
    }
    public static RootCapture rootCapture(Obj arguments) {
        Objects.requireNonNull(arguments);
        require(arguments.members().keySet().equals(java.util.Set.of("capture_context","public_arguments")),"exact typed ROOT capture wrapper required");
        require(arguments.get("public_arguments") instanceof Obj publicArgs&&publicArgs.members().isEmpty(),"ROOT has exactly empty native public arguments");
        try {return RootCapture.valueOf(text(arguments.get("capture_context"),"ROOT capture context"));}
        catch(IllegalArgumentException unknown){throw new IllegalArgumentException("unknown typed ROOT capture context",unknown);}
    }
    public enum Query {
        ROOT("query-campaign-root-context-v1"),
        CASH("query-war-cash-current-resources-v1"),
        MERCENARIES("query-player-mercenary-context-v1"),
        CONSTRUCTION("g2_player_construction_view_probe_v1"),
        FACTION_GIFT("private-query-faction-gift-member-v1"),
        FACTION_ALERTS("query-player-faction-alerts-v1"),
        FACTION_GIFT_RECEIPT("private-query-faction-gift-receipt-v1"),
        FEAST_DIAGNOSTIC("query-activity-planner-diag-v1-private"),
        FEAST_INPUTS("query-activity-feast-stage5-start-inputs-v1-private"),
        FEAST_HOSTED("query-activity-feast-hosted-post-v1-private");
        private final OperationKey operation;
        Query(String operation) { this.operation = new OperationKey(operation); }
        public OperationKey operation() { return operation; }
    }
    /** Actual root registration, never guessed from a prefix or an analysis capability. */
    public record Permission(Optional<String> capability, String permissionKey,
            ReadContract.PermissionMode mode, ReadContract.WireProfile wireProfile) {
        public Permission { Objects.requireNonNull(capability); capability.ifPresent(StrictJson::text);
            StrictJson.text(permissionKey); Objects.requireNonNull(mode); Objects.requireNonNull(wireProfile);
            require((mode == ReadContract.PermissionMode.ADVERTISED_CAPABILITY) == capability.isPresent(),
                    "actual public capability or exact source-qualified private permission required"); }
    }
    public record Registration(ExactRef definitionSource, Permission permission) {
        public Registration { Objects.requireNonNull(definitionSource); Objects.requireNonNull(permission);
            require(definitionSource.bytes() > 0, "actual exact query producer source required"); }
    }
    @FunctionalInterface public interface Registrations { Registration exact(Query query); }
    /** Root adapts the one installed strict Activity read; this port never creates another native contract. */
    public interface ExternalFeastInputs {
        PlanningReadResult<PlanningReadReceipt> read(PlanningRequest request);
        PlanningReadResult<PlanningReadReceipt> read(Session borrowed,PlanningRequest request);
    }
    /** The identical source-bound M1 family supplies both live and cold original-receipt validation. */
    public interface ExternalFactionAlerts {
        ExactRef definitionSource();
        PlanningReadResult<PlanningReadReceipt> read(PlanningRequest request);
        PlanningReadResult<PlanningReadReceipt> read(Session borrowed,PlanningRequest request);
        void verifyOriginal(PlanningReadReceipt original,Obj actualArchivedSnapshot);
    }

    /** A transport observation only. Each original domain codec must still validate the result. */
    public static final class Packet {
        private final PlanningReadReceipt receipt;
        private final Obj result;
        private final Obj originalResult;
        private Packet(PlanningReadReceipt receipt, Obj result,Obj originalResult) { this.receipt = receipt; this.result = result;this.originalResult=originalResult; }
        public PlanningReadReceipt receipt() { return receipt; }
        public Obj result() { return result; }
        public Obj originalResult() { return originalResult; }
        public byte[] originalFrame() { return receipt.original().originalFrame().bytes(); }
    }
    private final EnumMap<Query, ReadContract<Packet>> contracts = new EnumMap<>(Query.class);
    private final ReadContract<Packet> mercenaryEmployer;
    private final Optional<ExternalFeastInputs> externalFeastInputs;
    private final Optional<ExternalFactionAlerts> externalFactionAlerts;
    public FinanceReadContracts(Registrations actualRegistrations) {
        this(actualRegistrations,Optional.empty(),Optional.empty());
    }
    public FinanceReadContracts(Registrations actualRegistrations,ExternalFeastInputs externalFeastInputs) {
        this(actualRegistrations,Optional.of(Objects.requireNonNull(externalFeastInputs)),Optional.empty());
    }
    public FinanceReadContracts(Registrations actualRegistrations,ExternalFeastInputs externalFeastInputs,ExternalFactionAlerts externalFactionAlerts) {
        this(actualRegistrations,Optional.of(Objects.requireNonNull(externalFeastInputs)),Optional.of(Objects.requireNonNull(externalFactionAlerts)));
    }
    private FinanceReadContracts(Registrations actualRegistrations,Optional<ExternalFeastInputs> externalFeastInputs,Optional<ExternalFactionAlerts> externalFactionAlerts) {
        Objects.requireNonNull(actualRegistrations);
        this.externalFeastInputs=Objects.requireNonNull(externalFeastInputs);
        this.externalFactionAlerts=Objects.requireNonNull(externalFactionAlerts);
        for (Query query : Query.values()) {
            if(externalFeastInputs.isPresent()&&(query==Query.FEAST_DIAGNOSTIC||query==Query.FEAST_INPUTS||query==Query.FEAST_HOSTED))continue;
            if(externalFactionAlerts.isPresent()&&query==Query.FACTION_ALERTS)continue;
            Registration registration = Objects.requireNonNull(actualRegistrations.exact(query), "explicit original query registration required");
            Permission permission = registration.permission();
            java.util.function.BiFunction<PlanningReadRequest,String,NativeRequest> prepare=(request,requestId) -> {
                        if(query==Query.ROOT)rootCapture(request.arguments());
                        else StrictJson.require(request.arguments().members().isEmpty(), "this fixed original query takes no additional request fields");
                        var fields = new java.util.LinkedHashMap<String,Value>();
                        if(query==Query.CASH) {
                            fields.put("expected_snapshot_revision",new IntegerValue(request.before().frame().identity().nativeRevision()));
                        }
                        if (query == Query.FACTION_GIFT || query == Query.FACTION_GIFT_RECEIPT || query == Query.FEAST_DIAGNOSTIC
                                || query == Query.FEAST_INPUTS || query == Query.FEAST_HOSTED) {
                            fields.put("expected_date_raw", new IntegerValue(request.before().frame().identity().dateRaw()));
                            fields.put((query == Query.FACTION_GIFT || query == Query.FACTION_GIFT_RECEIPT) ? "expected_player_character_id" : "expected_actor_character_id",
                                    new IntegerValue(request.before().frame().identity().player()));
                        }
                        if (query == Query.FEAST_INPUTS) {
                            fields.put("expected_activity_key", new Text("activity_feast"));
                            fields.put("expected_option_key", new Text("feast_type_generic"));
                            fields.put("expected_planning_stage", new IntegerValue(java.math.BigInteger.valueOf(5)));
                        }
                        return new NativeRequest(query.operation().value(), permission.capability(), new RawJson(encode(new Obj(fields))));
                    };
            java.util.function.Function<PlanningReadReceipt,Packet> decode=receipt->decode(query,receipt);
            ReadContract<Packet> contract=query==Query.ROOT
                    ?new ReadContract<>(ROOT_CONTRACT_ID,query.operation(),permission.capability(),permission.permissionKey(),permission.mode(),permission.wireProfile(),
                        ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,registration.definitionSource(),prepare,decode,decode,FinanceReadContracts::requireRootReuse)
                    :new ReadContract<>("ordinary-finance-read:"+query.name(),query.operation(),permission.capability(),permission.permissionKey(),permission.mode(),permission.wireProfile(),
                        ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,registration.definitionSource(),prepare,decode,decode);
            contracts.put(query, contract);
        }
        var market=contract(Query.MERCENARIES);
        mercenaryEmployer=new ReadContract<>(MERCENARY_EMPLOYER_CONTRACT_ID,market.operation(),market.requiredCapability(),
                market.permissionKey(),market.permissionMode(),market.wireProfile(),ReadContract.GuardMode.RECONCILIATION_OBSERVATION,
                market.sourceRef(),(request,requestId)->{
                    require(request.origin() instanceof CommandOrigin.Reconciliation,"mercenary employer read requires its original pending phase");
                    mercenaryFrame(request);
                    return new NativeRequest(market.operation().value(),market.requiredCapability(),new RawJson(encode(request.arguments())));
                },receipt->decode(Query.MERCENARIES,receipt),receipt->decode(Query.MERCENARIES,receipt));
    }
    public List<ReadContract<?>> registeredContracts() {
        var result=new java.util.ArrayList<ReadContract<?>>(contracts.values());result.add(mercenaryEmployer);return List.copyOf(result);
    }
    public ReadContract<Packet> mercenaryEmployerContract() { return mercenaryEmployer; }
    /** Factual DATA only; the actual coordinator still owns read admission and the canonical pending action. */
    public static org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity mercenaryFrame(PlanningReadRequest request) {
        require(request.operation().equals(Query.MERCENARIES.operation())&&request.arguments().members().isEmpty(),
                "exact empty mercenary current-player query required");
        if(request.origin() instanceof CommandOrigin.Reconciliation)return request.reconciliationBefore();
        require(request.origin() instanceof CommandOrigin.Gameplay,"mercenary market requires gameplay or its original-pending observation");
        return request.before();
    }
    public static void requireMercenaryEmployerProfile(ReadContract<?> actual) {
        String capability="game.command."+Query.MERCENARIES.operation().value();
        require(actual.contractId().equals(MERCENARY_EMPLOYER_CONTRACT_ID)&&actual.operation().equals(Query.MERCENARIES.operation())
                &&actual.guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                &&actual.permissionMode()==ReadContract.PermissionMode.ADVERTISED_CAPABILITY
                &&actual.requiredCapability().filter(capability::equals).isPresent()&&actual.permissionKey().equals(capability)
                &&actual.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP&&actual.hasPureReplay(),
                "only the installed independent mercenary employer read profile is eligible");
    }
    public ReadContract<Packet> contract(Query query) { return Objects.requireNonNull(contracts.get(query)); }
    public ExactRef definitionSource(Query query) {
        return query==Query.FACTION_ALERTS&&externalFactionAlerts.isPresent()?externalFactionAlerts.orElseThrow().definitionSource():contract(query).sourceRef();
    }
    /** An archived receipt is decoded against the exact installed owner, never a newly guessed same-operation contract. */
    public Packet decodeOriginal(Query query,PlanningReadReceipt original,Obj actualSnapshot) {
        if(query==Query.FACTION_ALERTS&&externalFactionAlerts.isPresent())externalFactionAlerts.orElseThrow().verifyOriginal(original,actualSnapshot);
        else if(query==Query.MERCENARIES&&original.request().origin() instanceof CommandOrigin.Reconciliation)
            return mercenaryEmployer.replay(original);
        else return contract(query).replay(original);
        return decode(query,original);
    }
    /** Owning fixed-receipt DATA parser for canonical archived Gift history. This is not an installed
     * contract or current read permission; the caller must separately prove actual archive and writer membership. */
    public static Packet decodeArchivedGiftReceipt(PlanningReadReceipt original) {
        require(original.contractId().equals("ordinary-finance-read:"+Query.FACTION_GIFT_RECEIPT.name())
                &&original.request().operation().equals(Query.FACTION_GIFT_RECEIPT.operation())
                &&original.request().arguments().members().isEmpty(),"exact original fixed Gift receipt contract required");
        return decode(Query.FACTION_GIFT_RECEIPT,original);
    }
    public PlanningReadResult<Packet> read(Query query, PlanningReadPort originalPort, PlanningRequest request) {
        if(query==Query.FEAST_INPUTS&&externalFeastInputs.isPresent())return external(Query.FEAST_INPUTS,externalFeastInputs.orElseThrow().read(request),request);
        if(query==Query.FACTION_ALERTS&&externalFactionAlerts.isPresent())return external(Query.FACTION_ALERTS,externalFactionAlerts.orElseThrow().read(request),request);
        return Objects.requireNonNull(originalPort).read(contract(query),
                new PlanningReadRequest(request.before(), request.source(), request.sessionId(),
                        query.operation(), query==Query.ROOT?rootArguments(RootCapture.PUBLIC_QUERY):new Obj(java.util.Map.of()), request.deadline()));
    }
    /** Final-lock consumers must borrow the original writer; this never opens another transaction. */
    public PlanningReadResult<Packet> read(Session borrowed, Query query, PlanningReadPort originalPort, PlanningRequest request) {
        if(query==Query.FEAST_INPUTS&&externalFeastInputs.isPresent())return external(Query.FEAST_INPUTS,externalFeastInputs.orElseThrow().read(Objects.requireNonNull(borrowed),request),request);
        if(query==Query.FACTION_ALERTS&&externalFactionAlerts.isPresent())return external(Query.FACTION_ALERTS,externalFactionAlerts.orElseThrow().read(Objects.requireNonNull(borrowed),request),request);
        return Objects.requireNonNull(originalPort).read(Objects.requireNonNull(borrowed), contract(query),
                new PlanningReadRequest(request.before(), request.source(), request.sessionId(),
                        query.operation(), query==Query.ROOT?rootArguments(RootCapture.PUBLIC_QUERY):new Obj(java.util.Map.of()), request.deadline()));
    }
    private PlanningReadResult<Packet> external(Query query,PlanningReadResult<PlanningReadReceipt> result,PlanningRequest request) {
        Objects.requireNonNull(result);
        if(result instanceof PlanningReadResult.Known<PlanningReadReceipt> known) {
            var original=known.value();require(original.equals(known.receipt())&&original.request().before().equals(request.before())
                    &&original.request().source().equals(request.source())&&original.request().sessionId().equals(request.sessionId())
                    &&original.request().deadline().equals(request.deadline())&&original.request().operation().equals(query.operation()),"strict owner read crossed original complete source/frame/session/deadline");
            if(query==Query.FACTION_ALERTS)externalFactionAlerts.orElseThrow().verifyOriginal(original,request.observations().snapshot());
            return new PlanningReadResult.Known<>(decode(query,original),original,known.originalReceipt());
        }
        var unavailable=(PlanningReadResult.Unavailable<PlanningReadReceipt>)result;
        return new PlanningReadResult.Unavailable<>(unavailable.reason(),unavailable.original());
    }
    private static Packet decode(Query query, PlanningReadReceipt receipt) {
        if(query==Query.ROOT) {require(ROOT_CONTRACT_ID.equals(receipt.contractId()),"exact versioned ROOT capture contract required");rootCapture(receipt.request().arguments());}
        byte[] packet=receipt.original().originalPacket(),originalFrame=receipt.original().originalFrame().bytes();
        require(receipt.original().nativeOk()&&receipt.original().requestId().equals(receipt.requestId())&&packet.length>=5
                &&java.nio.ByteBuffer.wrap(packet,0,4).order(java.nio.ByteOrder.LITTLE_ENDIAN).getInt()==packet.length-4
                &&java.util.Arrays.equals(java.util.Arrays.copyOfRange(packet,4,packet.length),originalFrame),"original finance Native packet length/frame/request differs");
        Obj frame = org.xar.ck3.control.application.driver.DriverJson.object(originalFrame,RawJson.MAXIMUM_BYTES);
        require(new Text("command_result").equals(frame.get("type"))
                && new IntegerValue(java.math.BigInteger.ONE).equals(frame.get("protocol_version"))
                && new Text(receipt.requestId()).equals(frame.get("request_id"))
                && new Bool(true).equals(frame.get("ok")), "original native read envelope mismatch");
        Obj result = object(frame.get("result"), "native query result");
        // CONSTRUCTION owns source_red for a returned mapping with different step/admission.
        // Keep the complete framed result; its sole domain reducer decides source validity.
        if(query!=Query.CONSTRUCTION)require(new Text(query.operation().value()).equals(result.get("step"))
                && new Bool(true).equals(result.get("accepted")), "native query step or admission mismatch");
        require(receipt.original().originalResultToken().isPresent()
                && org.xar.ck3.control.application.driver.DriverJson.object(receipt.original().originalResultToken().orElseThrow().bytes(),RawJson.MAXIMUM_BYTES).equals(result),
                "original native result token differs from complete frame");
        Obj normalized=query==Query.ROOT?CampaignRootContextJson.normalizeNativeResult(result,receipt.request().before().frame().identity().dateRaw(),
                receipt.request().before().frame().identity().nativeRevision()):result;
        return new Packet(receipt, normalized,result);
    }
    /** DATA equivalence only. The sole canonical publisher must independently prove unchanged native bytes and READ-only lineage. */
    private static void requireRootReuse(PlanningReadReceipt original,Packet decoded,PlanningReadRequest current,Obj currentSemantic) {
        require(decoded.receipt().equals(original)&&ROOT_CONTRACT_ID.equals(original.contractId())
                &&rootCapture(original.request().arguments())==RootCapture.PUBLIC_QUERY&&rootCapture(current.arguments())==RootCapture.PUBLIC_QUERY,
                "only the identical public ROOT original can enter canonical reuse");
        var before=original.request().before();var after=current.before();var old=before.frame();var fresh=after.frame();
        require(original.request().operation().equals(Query.ROOT.operation())&&current.operation().equals(Query.ROOT.operation())
                &&original.request().source().equals(current.source())&&original.request().sessionId().equals(current.sessionId())
                &&before.machineId().equals(after.machineId())&&before.game().equals(after.game())&&before.observationVersion()==after.observationVersion()
                &&old.episodeRunId().equals(fresh.episodeRunId())&&old.snapshotId().equals(fresh.snapshotId())&&old.identity().equals(fresh.identity())
                &&java.time.Instant.now().isBefore(current.deadline()),"public ROOT reuse crossed original Game/source/session/native frame or current deadline");
        require(new Text(fresh.snapshotId()).equals(currentSemantic.get("snapshot_id"))&&new IntegerValue(fresh.revision()).equals(currentSemantic.get("revision"))
                &&new IntegerValue(fresh.identity().nativeRevision()).equals(currentSemantic.get("native_revision"))
                &&new IntegerValue(fresh.identity().dateRaw()).equals(currentSemantic.get("date_raw"))
                &&new Text(fresh.episodeRunId()).equals(currentSemantic.get("episode_run_id"))
                &&new IntegerValue(fresh.identity().player()).equals(object(currentSemantic.get("played_character"),"actual ROOT current player").get("character_id")),
                "public ROOT reuse lacks the actual complete current semantic identity");
        require(CampaignRootContextJson.normalizeNativeResult(decoded.originalResult(),fresh.identity().dateRaw(),fresh.identity().nativeRevision()).equals(decoded.result()),
                "public ROOT original projection changed under the current exact decoder");
        Obj root=object(decoded.result().get("campaign_root_context"),"original normalized ROOT context");
        require(!new Text("available").equals(root.get("status"))
                ||new IntegerValue(fresh.identity().player()).equals(root.get("player_character_id")),
                "available public ROOT original belongs to another current player");
    }
}


