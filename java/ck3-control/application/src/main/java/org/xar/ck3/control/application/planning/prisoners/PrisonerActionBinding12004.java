package org.xar.ck3.control.application.planning.prisoners;

import static org.xar.ck3.control.application.planning.prisoners.PrisonerPlanningPorts.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004.*;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.*;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;

/** Pure command factory and archive-backed preparation. It has no native submit or ledger writer. */
public final class PrisonerActionBinding12004 implements CommandBinding, ActionPorts.PreparationPort {
    public static final String SCHEMA = "xar.java.prisoner-independent-effect/v1";
    public static final String PUBLIC_SCHEMA="xar.java.prisoner-public-submit/v1";
    private static final Set<String> COMMON = Set.of("prisoner_character_id", "selected_collection_read", "active_war_ids", "war_retention_reads");
    private final ActionPorts.OutcomeArchive archive;
    private final Queries queries;
    public PrisonerActionBinding12004(ActionPorts.OutcomeArchive archive, Queries queries) {
        this.archive = Objects.requireNonNull(archive); this.queries = Objects.requireNonNull(queries);
    }
    public PrisonerActionBinding12004 withArchive(ActionPorts.OutcomeArchive actualLockedArchive) {
        return new PrisonerActionBinding12004(Objects.requireNonNull(actualLockedArchive), queries);
    }
    @Override public NativeRequest prepare(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed,
            ActionCommand command, String requestId) {
        Objects.requireNonNull(borrowed); StrictJson.text(requestId);
        return withArchive(archive.withSession(borrowed)).prepare(command);
    }
    @Override public Optional<ActionCommand> bind(PlanningRequest request, OperationKey operation,
            OpportunityJson.Obj arguments, Claims claims, OpportunityJson.Obj originalChoice) {
        Objects.requireNonNull(request); Objects.requireNonNull(originalChoice);
        requireOperation(operation); ObjectNode args = object(arguments); fields(operation, args);
        StrictJson.require(!args.has("submission_schema"),"ordinary policy cannot author the public primitive route");
        long prisoner = id(args.get("prisoner_character_id"));
        StrictJson.require(claims.equals(claims(prisoner, request.before().frame().identity().player().longValueExact())), "exact prisoner resource claims required");
        StrictJson.require(ExactRef.fromJson(args.get("selected_collection_read")).equals(ExactRef.fromJson(
                StrictJson.parse(OpportunityJson.encode(originalChoice)).get("collection_read_receipt"))), "selected collection original differs from command");
        var frame = PrisonerCollector12004.frame(request);
        StrictJson.require(warIds(args).equals(frame.activeWarIds()), "command active wars differ from actual planning snapshot");
        if (operation.equals(PrisonerOrdinaryPolicy12004.RANSOM)) StrictJson.require(
                signed(args.get("pre_player_gold_raw")).equals(gold(request.observations().snapshot())), "ransom wallet baseline differs from current native snapshot");
        ObjectNode identity = StrictJson.object().put("machine_id", request.before().machineId())
                .put("session_id", request.sessionId()).put("episode_run_id", request.before().frame().episodeRunId())
                .put("snapshot_id", request.before().frame().snapshotId()).put("revision", request.before().frame().revision())
                .put("operation", operation.value());
        identity.set("game", request.before().game().toJson()); identity.set("arguments", args);
        String actionId = "prisoner:" + PrisonerVanillaResearch.sha256(StrictJson.canonical(identity));
        return Optional.of(new ActionCommand(actionId, request.before(), request.source(), request.sessionId(), operation, arguments,
                expected(request.before(), request.source(), operation, prisoner), claims, request.deadline()));
    }
    public static ExpectedPostcondition expected(ObservationIdentity before, org.xar.ck3.control.g2.common.G2Source source,
            OperationKey operation, long prisoner) {
        requireOperation(operation); Objects.requireNonNull(before); Objects.requireNonNull(source);
        StrictJson.require(prisoner > 0 && prisoner < 0xffffffffL && BigInteger.valueOf(prisoner).compareTo(before.frame().identity().player()) != 0,
                "distinct valid full prisoner identity required");
        return new ExpectedPostcondition(1, before, source, SCHEMA, List.of(
                new ExpectedInteger(new FieldKey("prisoner.target_id"), BigInteger.valueOf(prisoner)),
                new ExpectedBoolean(new FieldKey(operation.equals(PrisonerOrdinaryPolicy12004.RANSOM)
                        ? "prisoner.ransom_material_observed" : "prisoner.freedom_observed"), true),
                new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true)));
    }
    @Override public NativeRequest prepare(ActionCommand command) {
        requireOperation(command.operation()); ObjectNode args = object(command.arguments()); fields(command.operation(), args);
        var original = selected(command); long prisoner = id(args.get("prisoner_character_id"));
        StrictJson.require(command.expected().equals(expected(command.before(), command.source(), command.operation(), prisoner)), "prisoner expected postcondition changed");
        boolean direct=isPublic(command);
        if(direct)return publicPrimitive(command,args,original,prisoner);
        var frame = new Frame(command.before().frame().revision(), command.before().frame().identity().nativeRevision(),
                command.before().frame().identity().dateRaw().intValueExact(), command.before().frame().identity().player().longValueExact(), warIds(args));
        StrictJson.require(!retained(command, frame, prisoner, args), "current complete war proof retains selected prisoner");
        var projection = ReleaseCollectionProjection12003.decode(original.normalized().bytes(), ReleaseCollectionProjection12003.SupportedBuild.CK3_12004, frame.binding(prisoner));
        StrictJson.require(projection.selectedOrdinal() == original.ordinal(), "prepared selected collection ordinal differs");
        ObjectNode wire = StrictJson.object().put("prisoner_character_id", prisoner);
        if (command.operation().equals(PrisonerOrdinaryPolicy12004.RELEASE)) {
            var query = new CollectionQuery(original.contract(), original.intent());
            var entry = new PrisonerCollector12004.Entry(original.normalized(), query, projection, Optional.of(original.reference()));
            StrictJson.require(PrisonerCollector12004.acceptedRelease(entry, frame)
                    && !PrisonerCollector12004.positiveRansomPriority(entry, frame), "release final accepted offer or ransom priority changed");
            StrictJson.integer(args.get("release_query_sequence"), projection.querySequence(), projection.querySequence());
            StrictJson.integer(args.get("release_option_mask_bits"), query.mask(), query.mask());
            wire.put("release_query_sequence", projection.querySequence()).put("release_option_mask_bits", query.mask());
        } else {
            StrictJson.require(original.intent().options() instanceof PrisonerOptionIntent.Unconditional, "ordinary ransom cannot change authored release terms");
            JsonNode value = StrictJson.parse(original.normalized().bytes()).path("player_prisoner_collection");
            StrictJson.integer(value.get("played_dynasty_id"), BigInteger.ONE, StrictJson.UINT64_MAX);
            var row = projection.rows().get(original.ordinal());
            StrictJson.require(row.lineage() instanceof ReleaseCollectionProjection12003.MeasuredLineage lineage && !lineage.sameDynasty()
                    && row.childRelation() instanceof ReleaseCollectionProjection12003.MeasuredChildRelation child && !child.childOfPlayedCharacter()
                    && row.primaryTitleTier() instanceof ReleaseCollectionProjection12003.MeasuredTitleTier tier && (tier.raw() == null || tier.raw() == 1), "ordinary ransom eligibility changed");
            var quote = PrisonerVanillaResearch.readQuote(value.path("prisoners").get(original.ordinal()).get("ransom_quote_preview"), frame.binding(prisoner), projection.proofEpoch());
            StrictJson.require(quote instanceof PrisonerVanillaResearch.AvailableQuote, "actual final ransom quote unavailable");
            var available = (PrisonerVanillaResearch.AvailableQuote) quote;
            StrictJson.require(available.wouldAcceptNow(), "recipient refuses actual final ransom quote");
            StrictJson.integer(args.get("quote_query_sequence"), projection.querySequence(), projection.querySequence());
            StrictJson.integer(args.get("payer_character_id"), available.payerCharacterId(), available.payerCharacterId());
            StrictJson.integer(args.get("quoted_gold_raw"), available.quotedGoldRaw(), available.quotedGoldRaw());
            StrictJson.require(StrictJson.text(args.get("selected_option")).equals(available.option().name().toLowerCase(java.util.Locale.ROOT))
                    && bool(args.get("amount_is_acceptance_time_quote")) == available.amountIsAcceptanceTimeQuote(), "ransom option timing differs from actual final quote");
            wire.put("quote_query_sequence", projection.querySequence()).put("payer_character_id", available.payerCharacterId()).put("quoted_gold_raw", available.quotedGoldRaw());
        }
        return new NativeRequest(command.operation().value(), Optional.empty(), new RawJson(StrictJson.canonical(wire)));
    }
    public record SelectedRead(ExactRef reference, PlanningReadReceipt receipt, ReadContract<RawJson> contract,
            RawJson normalized, int ordinal, PrisonerOptionIntent.Arguments intent) {
        public SelectedRead { Objects.requireNonNull(reference); Objects.requireNonNull(receipt); Objects.requireNonNull(contract);
            Objects.requireNonNull(normalized); Objects.requireNonNull(intent);
            StrictJson.require(reference.bytes() > 0 && ordinal >= 0 && ordinal < 64, "actual selected read and bounded ordinal required"); }
    }
    public SelectedRead selected(ActionCommand command) {
        ObjectNode args = object(command.arguments()); ExactRef reference = ExactRef.fromJson(args.get("selected_collection_read"));
        PlanningReadReceipt read = archive.loadRead(reference);
        StrictJson.require(archive.readReferenceOf(read).equals(reference), "selected collection archive identity changed");
        int ordinal = -1;
        for (int index = 0; index < 64; index++) if (queries.collections().get(index).operation().equals(read.request().operation())) ordinal = index;
        StrictJson.require(ordinal >= 0, "selected original is not a registered native-family collection");
        ReadContract<RawJson> contract = queries.collections().get(ordinal); requireOriginal(command, contract, read);
        if(isPublic(command))read.original().custody().orElseThrow(()->new IllegalArgumentException("actual public collection request custody is absent")).verify(read);
        var intent = PrisonerOptionIntent.decode(OpportunityJson.encode(read.request().arguments()));
        var normalized=contract.replay(read);
        if(isPublic(command)&&command.operation().equals(PrisonerOrdinaryPolicy12004.RANSOM)){
            long target=id(args.get("prisoner_character_id"));var rows=StrictJson.parse(normalized.bytes()).path("player_prisoner_collection").get("prisoners");
            int selected=-1;for(int i=0;i<rows.size();i++)if(id(rows.get(i).get("prisoner_character_id"))==target){StrictJson.require(selected<0,"public target must be unique");selected=i;}
            StrictJson.require(selected>=0,"public ransom target absent from actual collection");ordinal=selected;
        }
        return new SelectedRead(reference, read, contract, normalized, ordinal, intent);
    }
    private boolean retained(ActionCommand command, Frame frame, long prisoner, ObjectNode args) {
        JsonNode refs = args.get("war_retention_reads"); StrictJson.require(refs != null && refs.isArray() && refs.size() == frame.activeWarIds().size(), "all active war original reads required");
        for (int index = 0; index < frame.activeWarIds().size(); index++) {
            long war = frame.activeWarIds().get(index); ReadContract<RawJson> contract = queries.wars().get(war);
            StrictJson.require(contract != null, "active war exact registered contract absent");
            ExactRef reference = ExactRef.fromJson(refs.get(index)); PlanningReadReceipt read = archive.loadRead(reference);
            StrictJson.require(archive.readReferenceOf(read).equals(reference) && read.request().arguments().equals(EMPTY), "war original archive/arguments changed");
            requireOriginal(command, contract, read);
            var proof = PrisonerRansomFormalPolicy12004.readWar(contract.decode(read).bytes(), frame, war);
            if (!(proof instanceof KnownWarRetention known) || known.retainedPrisonerIds().contains(prisoner)) return true;
        }
        return false;
    }
    private static void requireOriginal(ActionCommand command, ReadContract<RawJson> contract, PlanningReadReceipt read) {
        StrictJson.require(selectedFrameMatches(command,read) && read.request().source().equals(command.source())
                && read.request().sessionId().equals(command.sessionId()) && read.request().operation().equals(contract.operation())
                && read.contractId().equals(contract.contractId()) && read.original().nativeOk(), "selected original crossed full command/source/session frame");
    }
    private static List<Long> warIds(ObjectNode args) {
        JsonNode rows = args.get("active_war_ids"); StrictJson.require(rows != null && rows.isArray() && rows.size() <= 64, "actual bounded active war IDs required");
        List<Long> result = new ArrayList<>(); Set<Long> seen = new HashSet<>();
        for (JsonNode row : rows) { long value = id(row); StrictJson.require(seen.add(value), "duplicate active war ID"); result.add(value); }
        return List.copyOf(result);
    }
    private static void fields(OperationKey operation, ObjectNode args) {
        boolean direct=args.has("submission_schema");
        if(direct)StrictJson.require(PUBLIC_SCHEMA.equals(StrictJson.text(args.get("submission_schema"))),"exact public prisoner submission schema required");
        Set<String> fields = new HashSet<>(direct?Set.of("prisoner_character_id","selected_collection_read","submission_schema"):COMMON);
        fields.addAll(operation.equals(PrisonerOrdinaryPolicy12004.RANSOM)
                ? Set.of("quote_query_sequence", "payer_character_id", "quoted_gold_raw", "selected_option", "amount_is_acceptance_time_quote", "pre_player_gold_raw")
                : Set.of("release_query_sequence", "release_option_mask_bits"));
        StrictJson.object(args, fields);
    }
    public static boolean isPublic(ActionCommand command){var args=object(command.arguments());if(!args.has("submission_schema"))return false;
        StrictJson.require(PUBLIC_SCHEMA.equals(StrictJson.text(args.get("submission_schema"))),"exact public prisoner submission schema required");return true;}
    /** The public contract uses the actual new command frame; its real original read keeps its own public READ revision. */
    public static boolean selectedFrameMatches(ActionCommand command,PlanningReadReceipt read) {
        if(!isPublic(command))return read.request().before().equals(command.before());
        var original=read.request().before();var current=command.before();
        return original.machineId().equals(current.machineId())&&original.game().equals(current.game())
                &&original.observationVersion()==current.observationVersion()
                &&original.frame().episodeRunId().equals(current.frame().episodeRunId())
                &&original.frame().snapshotId().equals(current.frame().snapshotId())
                &&original.frame().identity().equals(current.frame().identity())
                &&original.frame().revision().compareTo(current.frame().revision())<=0;
    }
    private static void requirePublicReleaseAcceptance(RawJson original,int ordinal,int mask,BigInteger epoch) {
        var row=StrictJson.parse(original.bytes()).path("player_prisoner_collection").path("prisoners").get(ordinal);
        var preview=row.get(mask==0?"unconditional_release_preview":"negotiated_release_preview");
        StrictJson.require(preview!=null&&preview.isObject(),"release prisoner lacks a currently accepted native offer");
        StrictJson.require("available".equals(StrictJson.text(preview.get("status"))),"release prisoner lacks a currently accepted native offer");StrictJson.trueValue(preview.get("can_send"));
        StrictJson.integer(preview.get("proof_epoch"),epoch,epoch);var acceptance=preview.get("acceptance");
        StrictJson.require(acceptance!=null&&acceptance.isObject()
                &&(acceptance.path("auto_accept").isBoolean()&&acceptance.path("auto_accept").booleanValue()
                    ||acceptance.path("would_accept_now").isBoolean()&&acceptance.path("would_accept_now").booleanValue()),
                "release prisoner lacks a currently accepted native offer");
    }
    private static NativeRequest publicPrimitive(ActionCommand command,ObjectNode args,SelectedRead original,long prisoner){
        var identity=command.before().frame().identity();var frame=new FrameBinding(identity.nativeRevision(),identity.dateRaw().intValueExact(),identity.player().longValueExact(),prisoner);
        if(command.operation().equals(PrisonerOrdinaryPolicy12004.RANSOM))return publicRansomRequest(args,original,prisoner,frame);
        var projection=ReleaseCollectionProjection12003.decode(original.normalized().bytes(),ReleaseCollectionProjection12003.SupportedBuild.CK3_12004,frame);
        StrictJson.require(projection.selectedOrdinal()==original.ordinal(),"release prisoner differs from the queried collection row");
        int mask=original.intent().options() instanceof PrisonerOptionIntent.Negotiated terms?terms.mask():0;
        requirePublicReleaseAcceptance(original.normalized(),original.ordinal(),mask,projection.proofEpoch());
        StrictJson.integer(args.get("release_query_sequence"),projection.querySequence(),projection.querySequence());StrictJson.integer(args.get("release_option_mask_bits"),mask,mask);
        return new NativeRequest(PrisonerOrdinaryPolicy12004.RELEASE.value(),Optional.empty(),new RawJson(StrictJson.canonical(StrictJson.object()
                .put("prisoner_character_id",prisoner).put("release_query_sequence",projection.querySequence()).put("release_option_mask_bits",mask))));
    }
    private static NativeRequest publicRansomRequest(ObjectNode args,SelectedRead original,long prisoner,FrameBinding frame){
        var root=StrictJson.parse(original.normalized().bytes());var value=root.path("player_prisoner_collection");
        StrictJson.integer(value.get("played_character_id"),frame.playerCharacterId(),frame.playerCharacterId());StrictJson.integer(value.get("date_raw"),frame.dateRaw(),frame.dateRaw());
        var quote=PrisonerVanillaResearch.readQuote(value.path("prisoners").get(original.ordinal()).get("ransom_quote_preview"),frame,
                StrictJson.integer(root.get("observation_revision"),BigInteger.ONE,StrictJson.UINT64_MAX));
        StrictJson.require(quote instanceof PrisonerVanillaResearch.AvailableQuote,"ransom prisoner lacks an exact native final gold offer");
        var available=(PrisonerVanillaResearch.AvailableQuote)quote;StrictJson.require(available.wouldAcceptNow(),"ransom recipient refuses the exact final gold offer");
        var sequence=StrictJson.integer(root.get("query_sequence"),BigInteger.ONE,StrictJson.UINT64_MAX);
        StrictJson.integer(args.get("quote_query_sequence"),sequence,sequence);StrictJson.integer(args.get("payer_character_id"),available.payerCharacterId(),available.payerCharacterId());
        StrictJson.integer(args.get("quoted_gold_raw"),available.quotedGoldRaw(),available.quotedGoldRaw());signed(args.get("pre_player_gold_raw"));
        StrictJson.require(StrictJson.text(args.get("selected_option")).equals(available.option().name().toLowerCase(java.util.Locale.ROOT))
                &&bool(args.get("amount_is_acceptance_time_quote"))==available.amountIsAcceptanceTimeQuote(),"public ransom copied terms differ");
        return new NativeRequest(PrisonerOrdinaryPolicy12004.RANSOM.value(),Optional.empty(),new RawJson(StrictJson.canonical(StrictJson.object()
                .put("prisoner_character_id",prisoner).put("payer_character_id",available.payerCharacterId()).put("quote_query_sequence",sequence).put("quoted_gold_raw",available.quotedGoldRaw()))));
    }
    public ActionCommand bindPublic(String actionId,ObservationIdentity before,org.xar.ck3.control.g2.common.G2Source source,
            String sessionId,java.time.Instant deadline,OpportunityJson.Obj actualSnapshot,
            PlanningReadResult.Known<RawJson> known,RawJson incoming,long prisoner,OperationKey operation) {
        requireOperation(operation);StrictJson.require(StrictJson.parse(known.value().bytes()).equals(StrictJson.parse(incoming.bytes())),
                "public collection differs from the last actual same-runtime original");
        var read=known.receipt();StrictJson.require(archive.readReferenceOf(read).equals(known.originalReceipt())
                &&read.request().source().equals(source)&&read.request().sessionId().equals(sessionId),"public collection lost its actual source/session original");
        for(var guard:List.of(read.before(),read.after()))if(guard.binding().validUntil().isBefore(deadline))deadline=guard.binding().validUntil();
        ObjectNode args=StrictJson.object().put("submission_schema",PUBLIC_SCHEMA).put("prisoner_character_id",prisoner);
        args.set("selected_collection_read",known.originalReceipt().toJson());var normalized=StrictJson.parse(known.value().bytes());
        StrictJson.require("available".equals(normalized.path("status").textValue()),"public submission lacks a complete current paused collection");
        int ordinal=-1;for(int i=0;i<64;i++)if(queries.collections().get(i).operation().equals(read.request().operation()))ordinal=i;
        StrictJson.require(ordinal>=0&&queries.collections().get(ordinal).replay(read).equals(known.value()),"public collection is not an actual identical installed native original");
        var rows=normalized.path("player_prisoner_collection").get("prisoners");StrictJson.require(rows!=null&&rows.isArray(),"complete current prisoner rows required");int matches=0,selected=-1;
        for(int i=0;i<rows.size();i++)if(id(rows.get(i).get("prisoner_character_id"))==prisoner){matches++;selected=i;}
        StrictJson.require(matches==1&&(operation.equals(PrisonerOrdinaryPolicy12004.RANSOM)||selected==ordinal),"public prisoner differs from its queried unique collection row");
        BigInteger sequence=StrictJson.integer(normalized.get("query_sequence"),BigInteger.ONE,StrictJson.UINT64_MAX);
        if(operation.equals(PrisonerOrdinaryPolicy12004.RELEASE)) {
            var intent=PrisonerOptionIntent.decode(OpportunityJson.encode(read.request().arguments()));
            int mask=intent.options() instanceof PrisonerOptionIntent.Negotiated terms?terms.mask():0;
            args.put("release_query_sequence",sequence).put("release_option_mask_bits",mask);
        }else{
            var quote=PrisonerVanillaResearch.readQuote(rows.get(selected).get("ransom_quote_preview"),
                    new FrameBinding(before.frame().identity().nativeRevision(),before.frame().identity().dateRaw().intValueExact(),before.frame().identity().player().longValueExact(),prisoner),
                    StrictJson.integer(normalized.get("observation_revision"),BigInteger.ONE,StrictJson.UINT64_MAX));
            StrictJson.require(quote instanceof PrisonerVanillaResearch.AvailableQuote,"ransom prisoner lacks an exact native final gold offer");var available=(PrisonerVanillaResearch.AvailableQuote)quote;
            args.put("quote_query_sequence",sequence).put("payer_character_id",available.payerCharacterId()).put("quoted_gold_raw",available.quotedGoldRaw())
                    .put("selected_option",available.option().name().toLowerCase(java.util.Locale.ROOT)).put("amount_is_acceptance_time_quote",available.amountIsAcceptanceTimeQuote())
                    .put("pre_player_gold_raw",gold(actualSnapshot));
        }
        var command=new ActionCommand(actionId,before,source,sessionId,operation,PrisonerPlanningPorts.object(StrictJson.canonical(args)),
                expected(before,source,operation,prisoner),claims(prisoner,before.frame().identity().player().longValueExact()),deadline);
        prepare(command);return command;
    }
    public static BigInteger gold(OpportunityJson.Obj snapshot) {
        JsonNode row = org.xar.ck3.control.contracts.FullJsonTree.parse(OpportunityJson.encode(snapshot), org.xar.ck3.control.contracts.FullJsonTree.MAXIMUM_BYTES).get("played_character_gold");
        StrictJson.require(row != null && row.isObject(), "observed player gold baseline absent");
        StrictJson.integer(row.get("scale"), 100000, 100000); return signed(row.get("raw"));
    }
    public static BigInteger signed(JsonNode value) { return StrictJson.integer(value, BigInteger.valueOf(Long.MIN_VALUE), BigInteger.valueOf(Long.MAX_VALUE)); }
    public static long id(JsonNode value) { return StrictJson.integer(value, 1, 0xfffffffeL); }
    private static ObjectNode object(OpportunityJson.Obj value) {
        JsonNode parsed = StrictJson.parse(OpportunityJson.encode(value));
        StrictJson.require(parsed instanceof ObjectNode, "actual JSON object required"); return (ObjectNode) parsed;
    }
    private static boolean bool(JsonNode value) { StrictJson.require(value != null && value.isBoolean(), "actual boolean required"); return value.booleanValue(); }
    public static void requireOperation(OperationKey operation) { Objects.requireNonNull(operation); StrictJson.require(operation.equals(PrisonerOrdinaryPolicy12004.RELEASE)
            || operation.equals(PrisonerOrdinaryPolicy12004.RANSOM), "exact current prisoner native operation required"); }
}
