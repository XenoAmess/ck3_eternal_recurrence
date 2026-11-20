package org.xar.ck3.markets.saveaudit;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.markets.acceptance.FollowupContracts;
import org.xar.ck3.markets.acceptance.FollowupObservationScripts;
import org.xar.ck3.markets.acceptance.FixtureEmitter;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.FilePins;
import org.xar.ck3.save.ProducerSources;
import org.xar.ck3.save.SaveContracts;
import org.xar.ck3.save.SaveContracts.Pin;
import org.xar.ck3.save.SaveJson;

/** Interprets existing pinned RawExactStories outputs; never opens a SAVE or operates CK3. */
public final class CapacityWindowReadback {
    private CapacityWindowReadback() { }
    static final long STREAM = 512L * 1024 * 1024;
    static final int RAW = 4 * 1024 * 1024;
    static final int RECORD = 512 * 1024;
    static final List<String> FIELDS = List.of("registered_coin_count", "resident_coin_count", "pending_coin_count", "active_coin_count",
            "new_listings_today", "active_orders_count", "futures_open_positions_count", "ai_count", "attention_count",
            "ai_work_today", "attention_work_today", "ai_decisions_today", "ai_queue_schema", "attention_queue_schema",
            "ai_queue_dirty", "attention_queue_dirty", "ai_queue_repair_count", "ai_queue_last_repair_date",
            "daily_attempt_count", "daily_attempt_script_date", "daily_attempt_prev_date", "daily_attempt_prev_date_present",
            "daily_attempt_entered_dispatch", "daily_rejected_count", "daily_raw_attempt_count", "daily_raw_script_date", "last_date", "fee_cents");
    static final Set<String> REQUIRED = Set.of("registered_coin_count", "resident_coin_count", "pending_coin_count", "active_coin_count",
            "active_orders_count", "futures_open_positions_count", "ai_count", "attention_work_today", "ai_work_today", "ai_decisions_today", "last_date");
    static final FinancialProjector.LayoutHypothesis LAYOUT = new FinancialProjector.LayoutHypothesis("1.21.0", "19",
            BigInteger.valueOf(100000), "story", "char", FinancialProjector.NumberIdentityEncoding.unsigned64OmittedZero);

    /** Exact original public allocation; all three checkpoints belong to this one run. */
    public record Request(int schemaVersion, String machineId, String runId, String repository,
                          String actorNativeId, String observerNativeId, String exchangeNativeId,
                          Pin currentContext, Pin frozenArgv, Pin preparedCase, Pin fixtureManifest,
                          Pin observerRequest, Pin originalD0Review, Pin originalHostReport,
                          Pin exactReaderSource, Pin exactReaderCompilation, List<CheckpointInput> checkpoints) {
        public Request {
            need(schemaVersion == 1, "capacity readback request version1 required");
            need(machineId != null && machineId.matches("[a-z0-9][a-z0-9-]{2,95}"), "explicit machine ID required");
            need(runId != null && runId.matches("[A-Za-z0-9][A-Za-z0-9-]{1,160}"), "explicit original run ID required");
            need(repository != null && Path.of(repository).isAbsolute(), "absolute repository required");
            id(actorNativeId); id(observerNativeId); id(exchangeNativeId);
            need(!observerNativeId.equals(exchangeNativeId), "observer/exchange cannot alias");
            for (Pin pin : List.of(currentContext, frozenArgv, preparedCase, fixtureManifest, observerRequest,
                    originalD0Review, originalHostReport, exactReaderSource, exactReaderCompilation)) Objects.requireNonNull(pin);
            checkpoints = List.copyOf(checkpoints);
            need(checkpoints.stream().map(CheckpointInput::offset).toList().equals(List.of(0, 30, 395)), "only original D0/D30/D395 checkpoints qualify");
        }
    }
    public record CheckpointInput(int offset, Pin archiveReceipt, List<Pin> rawReadbacks) {
        public CheckpointInput {
            need(List.of(0, 30, 395).contains(offset), "finite capacity checkpoint required");
            Objects.requireNonNull(archiveReceipt); rawReadbacks = List.copyOf(rawReadbacks);
            need(!rawReadbacks.isEmpty() && rawReadbacks.size() <= 28, "bounded existing16-story reader batches required");
            need(rawReadbacks.stream().map(Pin::path).distinct().count() == rawReadbacks.size(), "duplicate readback input");
        }
    }
    public record Observation(boolean available, List<BigInteger> values) {
        public Observation {
            values=List.copyOf(values); need(values.size()==(available?1:0),"missing is distinct from one observed integer including zero");
        }
        public Observation(boolean available,BigInteger value) { this(available,value==null?List.of():List.of(value)); }
        public BigInteger value() { need(available,"unavailable source has no numeric value");return values.getFirst(); }
    }
    public record Witness(String nativeId, String producerTokenSha256, String wholeAstSha256) {
        public Witness { id(nativeId); SaveContracts.digest(producerTokenSha256); SaveContracts.digest(wholeAstSha256); }
    }
    public record Day(int ordinal, long financialDay, long scriptDate, boolean measured,
                      Map<String, Observation> sources, Witness witness) {
        public Day { sources = Map.copyOf(sources); Objects.requireNonNull(witness); }
    }
    /** A complete record chain is deliberately not a tier, financial, timing, or Game acceptance. */
    public record Result(String schema, String status, String machineId, String runId, String actorNativeId,
                         String observerNativeId, String exchangeNativeId, int observationEpoch,
                         FollowupContracts.ScaleTier declaredTier, long originNativeDateRaw, long originFinancialDay,
                         long originScriptDate, int warmupRecords, int measuredRecords, List<Day> days,
                         List<Pin> inputPins, SaveAuditSources.Binding consumerSourceBinding,
                         boolean currentFrozenBindingVerified, boolean immutablePrefixVerified,
                         boolean capacityTierQualified, boolean performancePass, boolean financialCertified,
                         boolean actualGameAcceptance) {
        public Result {
            days = List.copyOf(days); inputPins = List.copyOf(inputPins);
            need(!capacityTierQualified && !performancePass && !financialCertified && !actualGameAcceptance,
                    "record integrity never grants unrelated business/performance acceptance");
        }
    }
    record Story(String id, Clausewitz.Block ast, Witness witness) { }
    record Snapshot(int offset, long nativeDateRaw, Clausewitz.Block actor, Clausewitz.Block globals,
                    Map<String, Story> stories) { Snapshot { stories = Map.copyOf(stories); } }
    record Binding(FollowupContracts.Request observer, String actorId, String observerId, String exchangeId) { }
    record Chain(long nativeOrigin, long financialOrigin, long scriptOrigin, List<Day> days) { }

    public static void main(String[] args) throws IOException {
        if (args.length != 4 || !args[0].equals("--request") || !args[2].equals("--output"))
            throw new IllegalArgumentException("--request PINNED_REQUEST.json --output NEW_RESULT.json required");
        Path requestPath = Path.of(args[1]).toRealPath(), output = Path.of(args[3]).toAbsolutePath().normalize();
        need(!Files.exists(output, LinkOption.NOFOLLOW_LINKS) && Files.isDirectory(output.getParent()), "existing parent and create-only result required");
        Pin requestPin = FilePins.pin(requestPath);
        Request request = SaveJson.read(read(requestPin, RAW), Request.class);
        Path repository = Path.of(request.repository()).toRealPath();
        need(!output.startsWith(repository), "result must remain outside the repository");
        Result result = consume(request, requestPin);
        FilePins.verify(requestPath, requestPin);
        byte[] bytes = SaveJson.write(result); need(bytes.length <= RAW, "result remains<=4MiB");
        Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
        System.out.println(new String(SaveJson.write(FilePins.pin(output)), StandardCharsets.UTF_8));
    }

    public static Result consume(Request request, Pin requestPin) throws IOException {
        need(SaveJson.read(read(requestPin,RAW),Request.class).equals(request),"public consumer request differs from its immutable input pin");
        Path repo = Path.of(request.repository()).toRealPath();
        SaveAuditSources.Binding loaded = SaveAuditSources.verify(repo);
        List<Pin> inputs = new ArrayList<>(); inputs.add(requestPin);
        Binding binding = verifyBinding(request, inputs);
        ProducerSources.Binding parser = loaded.saveCore();
        List<Pin> dependencies=loadedDependencies(); inputs.addAll(dependencies);
        List<Snapshot> snapshots = new ArrayList<>();
        for (CheckpointInput checkpoint : request.checkpoints()) snapshots.add(readCheckpoint(request, checkpoint, parser, dependencies, inputs));
        Chain chain = interpret(binding, snapshots);
        verifyD0OriginReview(request,chain.nativeOrigin(),inputs);
        verifyNativeDays(request, chain.nativeOrigin(), inputs);
        for (Pin pin : inputs) FilePins.verify(Path.of(pin.path()), pin);
        need(loaded.equals(SaveAuditSources.verify(repo)), "consumer/parser loaded-source closure changed");
        return new Result("ck3-capacity-record-window-integrity-v1", "RECORD_CHAIN_COMPLETE_NOT_CAPACITY_ACCEPTANCE",
                request.machineId(), request.runId(), binding.actorId(), binding.observerId(), binding.exchangeId(),
                binding.observer().observationEpoch(), binding.observer().scaleTier(), chain.nativeOrigin(), chain.financialOrigin(),
                chain.scriptOrigin(), 30, 365, chain.days(), inputs, loaded, true, true, false, false, false, false);
    }

    private static Binding verifyBinding(Request request, List<Pin> pins) throws IOException {
        JsonNode context = node(request.currentContext(), RAW, pins), frozen = node(request.frozenArgv(), RAW, pins);
        JsonNode prepared = node(request.preparedCase(), RAW, pins), manifest = node(request.fixtureManifest(), RAW, pins);
        readAndTrack(request.observerRequest(),65536,pins);
        FollowupContracts.Input input=FixtureEmitter.readInput(Path.of(request.observerRequest().path()));
        need(input instanceof FollowupContracts.Request,"actual schema2 follow-up request required");
        FollowupContracts.Request observer=(FollowupContracts.Request)input;
        FilePins.verify(Path.of(request.observerRequest().path()),request.observerRequest());
        verifyScopeIdentity(request,context,frozen,prepared,manifest,observer);
        Set<String> producers=Set.of("AcceptanceContracts.java","ObservationScripts.java","FixtureEmitter.java","AcceptanceCommand.java","FollowupContracts.java","FollowupObservationScripts.java");
        Set<String> observedProducers=new HashSet<>();
        for(JsonNode row:array(manifest,"producer_source_pins")) {
            Pin source=pin(row); String name=Path.of(source.path()).getFileName().toString();
            need(producers.contains(name) && observedProducers.add(name),"original six fixture producers required");
            Path expected=Path.of(request.repository()).resolve("mod_financial_markets/tools/src/main/java/org/xar/ck3/markets/acceptance").resolve(name).toAbsolutePath().normalize();
            need(expected.equals(Path.of(source.path()).toAbsolutePath().normalize()),"fixture producer escaped repository");
            byte[] bytes=readAndTrack(source,2*1024*1024,pins);
            try(var embedded=FollowupObservationScripts.class.getResourceAsStream("/producer-source/org/xar/ck3/markets/acceptance/"+name)) {
                need(embedded!=null && java.util.Arrays.equals(bytes,embedded.readNBytes(2*1024*1024+1)),"loaded fixture producer source differs");
            }
        }
        need(observedProducers.equals(producers),"complete original six producer source pins required");
        JsonNode review = node(request.originalD0Review(), RAW, pins);
        need(text(review,"run_id").equals(request.runId()) && text(review,"reviewer").equals("/root"), "original current-run D0 Root review required");
        JsonNode assertions = object(review,"assertions");
        need(truth(assertions,"actual_case_specific_observer_pins_scale_tier_settings_actual_inventory_and_external_timing_source"), "actual original scale/settings/timing review is required; no inferred settings");
        JsonNode awaiting = node(pin(review.get("awaiting")), RAW, pins);
        need(text(awaiting,"run_id").equals(request.runId()), "original D0 awaiting crossed run");
        List<Pin> evidence = new ArrayList<>();
        for (JsonNode row : array(review,"evidence")) {
            Pin p=pin(row); need(p.path().endsWith(".json") && p.bytes()<=64L*1024*1024,"bounded original JSON review evidence required; never open a SAVE");
            FilePins.verify(Path.of(p.path()),p); pins.add(p); evidence.add(p);
        }
        need(!evidence.isEmpty(), "D0 review must preserve actual original evidence");
        readAndTrack(request.exactReaderSource(),RECORD,pins);
        JsonNode compiled=node(request.exactReaderCompilation(),RAW,pins);
        need(text(compiled,"schema").equals("ck3-task-exact-stories-compiled-provenance-v1") && text(compiled,"machine_id").equals(request.machineId()),"existing same-machine RawExactStories compiled proof required");
        samePin(compiled.get("diagnostic_source"),request.exactReaderSource());
        JsonNode originalCompile=node(pin(compiled.get("original_compile_wait")),RAW,pins);
        need(truth(originalCompile,"actual_original_popen_wait") && integer(originalCompile,"returncode")==0,"actual original javac wait0 required");
        List<String> compileArgs=strings(array(originalCompile,"argv"));
        need(compileArgs.stream().filter(arg->arg.replace('\\','/').equals(request.exactReaderSource().path().replace('\\','/'))).count()==1,
                "original javac argv did not compile this exact reader source");
        List<JsonNode> classes=array(compiled,"class_outputs"); need(!classes.isEmpty() && classes.size()<=32,"actual bounded class pin closure required");
        Set<String> classPaths=new HashSet<>();
        for(JsonNode row:classes) { Pin p=pin(row.get("pin")); need(classPaths.add(p.path()) && p.path().endsWith(".class") && p.bytes()<=RECORD,"unique compiled class pin required");readAndTrack(p,RECORD,pins); }
        return new Binding(observer, request.actorNativeId(), request.observerNativeId(), request.exchangeNativeId());
    }

    static void verifyScopeIdentity(Request request,JsonNode context,JsonNode frozen,JsonNode prepared,
                                    JsonNode manifest,FollowupContracts.Request observer) throws IOException {
        need(observer.caseId() == FollowupContracts.Profile.AI_CAPACITY && observer.observationEpoch() >= 1 && observer.observationEpoch() <= 2,
                "only an actual current capacity protocol epoch1/2 fixture is supported");
        need(observer.actor().mode() == FollowupContracts.ActorMode.CURRENT_PLAYER, "current played actor binding required");
        need(observer.targets().contractId()==null && observer.targets().positionId()==null && observer.targets().debtId()==null
                && observer.targets().newsId()==null && observer.targets().indexId()==null,"capacity window does not import120day/debt/derivatives business targets");
        need(text(context,"schema").equals("ck3-mod-acceptance-run-context-v1") && text(context,"run_id").equals(request.runId())
                && text(context,"product").equals("financial-markets") && text(context,"case").equals("ai-capacity"), "current public capacity allocation required");
        samePin(context.get("prepared_case"), request.preparedCase()); samePin(context.get("frozen_argv"), request.frozenArgv());
        need(text(frozen,"run_id").equals(request.runId()) && text(frozen,"mod_key").equals("financial-markets")
                && text(frozen,"cell").equals("ai-capacity"), "frozen public scope differs");
        need(prepared.get("case_inputs").equals(context.get("case_inputs")), "prepared/current case inputs differ");
        samePin(prepared.path("case_inputs").get("prebuilt_fixture_manifest"), request.fixtureManifest());
        JsonNode files = object(frozen,"files"); frozenMember(files, request.preparedCase());
        need(text(manifest,"schema").equals("ck3-mod-acceptance-prebuilt-fixture-v1")
                && text(manifest,"product").equals("financial-markets") && text(manifest,"case_id").equals("ai-capacity")
                && text(manifest,"machine_id").equals(request.machineId()), "actual capacity fixture manifest required");
        Path fixture = Path.of(text(manifest,"fixture_root")).toAbsolutePath().normalize();
        need(Path.of(request.observerRequest().path()).toAbsolutePath().normalize().equals(fixture.resolve("_xfma_request.json")), "canonical original observer request required");
        content(object(manifest,"files").get("_xfma_request.json"), request.observerRequest());
        Path deployed = Path.of(text(frozen,"state_dir")).resolve("profile/mod-content/fixture");
        JsonNode inventory = object(manifest,"files"); need(inventory.size() >= 1 && inventory.size() <= 32, "bounded full fixture inventory required");
        Map<String,byte[]> rendered=FollowupObservationScripts.render(observer);
        Set<String> expectedNames=new HashSet<>(rendered.keySet());expectedNames.add("_xfma_request.json");
        Set<String> actualNames=new HashSet<>();inventory.fieldNames().forEachRemaining(actualNames::add);
        need(actualNames.equals(expectedNames),"complete real protocol1 fixture including post-finance hook is required");
        for(var source:rendered.entrySet()) need(integer(inventory.get(source.getKey()),"bytes")==source.getValue().length
                && text(inventory.get(source.getKey()),"sha256").equals(FilePins.sha256(source.getValue())),"actual fixture differs from loaded protocol1 producer: "+source.getKey());
        var names = inventory.fieldNames();
        while (names.hasNext()) {
            String relative = names.next();
            need(!relative.startsWith("/") && !relative.contains("\\") && !relative.contains(":")
                    && !List.of(relative.split("/",-1)).contains("..") && !List.of(relative.split("/",-1)).contains(""), "canonical fixture member required");
            JsonNode actual = files.get(deployed.resolve(relative).toAbsolutePath().normalize().toString());
            need(actual != null && actual.equals(inventory.get(relative)), "frozen mounted fixture member differs: " + relative);
        }
        need(flag(frozen,"--saved-campaign-player-id").equals(request.actorNativeId()), "actor differs from frozen saved-campaign identity");
    }

    static Snapshot readCheckpoint(Request request, CheckpointInput checkpoint,
                                           ProducerSources.Binding parser,List<Pin> dependencies,List<Pin> pins) throws IOException {
        JsonNode archive = node(checkpoint.archiveReceipt(),65536,pins);
        need(text(archive,"schema").equals("ck3-financial-checkpoint-archive-v1") && text(archive,"machine_id").equals(request.machineId())
                && truth(archive,"exact_copy") && !truth(archive,"same_file"), "independent actual checkpoint archive required");
        Pin save = pin(archive.get("archive")); need(save.bytes()>=4 && save.bytes()<=STREAM, "SAVE exceeds existing stream bounds");
        long date = integer(archive,"date_raw"); need(date>0 && date<=Integer.MAX_VALUE,"positive int32 Native checkpoint date required");
        JsonNode result = object(archive,"original_checkpoint_result");
        need(truth(result,"accepted") && text(result,"step").equals("save-checkpoint")
                && text(result.path("checkpoint"),"status").equals("saved") && truth(result.path("materialization"),"available")
                && integer(result.path("checkpoint"),"date_raw")==date && integer(result.path("checkpoint"),"size")==save.bytes()
                && text(result.path("checkpoint"),"sha256").equals(save.sha256()), "original physical checkpoint result differs");
        JsonNode original=node(pin(archive.get("original_checkpoint_receipt")),64*1024*1024,pins);
        JsonNode frozen=node(request.frozenArgv(),RAW,pins);
        need(text(original,"pipe").equals(flag(frozen,"--bridge-pipe")), "archive belongs to a different frozen Host pipe");
        Path physical=Path.of(text(result.path("checkpoint"),"path")).toAbsolutePath().normalize();
        need(physical.equals(Path.of(text(frozen,"state_dir")).resolve("profile/save games/xar_checkpoint.ck3").toAbsolutePath().normalize())
                && physical.equals(Path.of(text(archive,"requested_source_path")).toAbsolutePath().normalize()),"archive source differs from the frozen Game profile checkpoint");
        String pointer=text(archive,"result_json_pointer"); need(pointer.matches("/steps/[0-9]+/result") && original.at(pointer).equals(result), "original checkpoint pointer/result differs");
        Map<String,Story> stories=new LinkedHashMap<>(); Clausewitz.Block actor=null, globals=null;
        JsonNode metadata=null;
        for (Pin readback : checkpoint.rawReadbacks()) {
            JsonNode raw=node(readback,RAW,pins), r=object(raw,"request");
            need(integer(raw,"schemaVersion")==2 && text(raw,"machineId").equals(request.machineId())
                    && text(raw,"status").equals("UNQUALIFIED_EXACT_STORY_DIAGNOSTIC")
                    && truth(raw,"inputUnchangedAtGuards") && integer(raw,"fullStreamPasses")==1
                    && !truth(raw,"financialCertified") && !truth(raw,"sourceLayoutQualified") && !truth(raw,"actualGameAcceptance"), "existing actual RawExactStories output required");
            samePin(r.get("archiveReceipt"),checkpoint.archiveReceipt()); samePin(r.get("save"),save); samePin(r.get("readerSource"),request.exactReaderSource());
            need(integer(r,"expectedDateRaw")==date && integer(r,"schemaVersion")==2 && text(r,"machineId").equals(request.machineId()), "raw checkpoint/date/source scope differs");
            need(Path.of(text(r,"repository")).toAbsolutePath().normalize().equals(Path.of(request.repository()).toAbsolutePath().normalize()),"raw source repository differs");
            need(text(raw,"completeStreamSha256").equals(save.sha256()) && text(raw,"completeStreamBytes").equals(Long.toString(save.bytes()))
                    && raw.get("before").equals(raw.get("after")), "complete EOF/SHA and unchanged physical evidence required");
            JsonNode physicalFacts=object(raw,"before");
            need(integer(physicalFacts,"bytes")==save.bytes() && Path.of(text(physicalFacts,"realPath")).toAbsolutePath().normalize().equals(Path.of(save.path()).toAbsolutePath().normalize())
                    && !text(physicalFacts,"creationTime").isEmpty() && !text(physicalFacts,"modifiedTime").isEmpty(),"raw physical extent/path/attributes differ");
            String keyStatus=text(physicalFacts,"providerFileKeyStatus");JsonNode fileKey=physicalFacts.get("providerFileKey");
            need((keyStatus.equals("AVAILABLE") && fileKey!=null && fileKey.isTextual() && !fileKey.textValue().isEmpty())
                    || (keyStatus.equals("UNAVAILABLE") && fileKey!=null && fileKey.isTextual() && fileKey.textValue().isEmpty()),"explicit file-key availability required");
            need(raw.get("parserBinding").equals(SaveJson.read(SaveJson.write(parser),JsonNode.class)), "loaded shared parser source binding differs");
            Set<Pin> declaredDependencies=new HashSet<>();for(JsonNode value:array(r,"classpath")) need(declaredDependencies.add(pin(value)),"duplicate readback dependency");
            need(declaredDependencies.equals(Set.copyOf(dependencies)),"readback/consumer actual four loaded dependency JARs differ");
            List<String> selected=ids(array(r,"storyIds")); need(!selected.isEmpty() && selected.size()<=16 && selected.contains(request.observerNativeId()), "actual16-story CLI/observer-per-batch guard required");
            need(ids(array(r,"actorIds")).equals(List.of(request.actorNativeId())) && truth(raw,"actorTablePathObserved"), "actual current actor raw projection required");
            need(integer(raw,"exactStoryProjections")==selected.size() && integer(raw,"combinedSelectedTokenBytes")>=0
                    && integer(raw,"combinedSelectedTokenBytes")<=RAW, "raw capture/byte limit differs");
            need(array(raw,"projections").size()==2,"exact globals/metadata projection pair required");
            JsonNode limits=object(raw,"limits");
            need(integer(limits,"maxStreamBytes")==STREAM && integer(limits,"maxRecordBytes")==RECORD
                    && integer(limits,"maxCaptures")==64 && integer(limits,"maxTableRecords")==200000
                    && integer(limits,"maxSelectedTokenBytes")==RAW && integer(limits,"maxReportBytes")==RAW, "original reader bounds cannot be widened");
            List<JsonNode> actorRows=array(raw,"actors"); need(actorRows.size()==1 && text(actorRows.getFirst(),"id").equals(request.actorNativeId()), "one actual actor required");
            Clausewitz.Block nextActor=tokens(text(actorRows.getFirst(),"clausewitzTokens"));
            need(actor==null || actor.equals(nextActor), "actor changed between same-archive batches"); actor=nextActor;
            for(JsonNode projection:array(raw,"projections")) {
                if(text(projection,"name").equals("globals")) {
                    Clausewitz.Block next=tokens(text(projection,"clausewitzTokens")); need(globals==null || globals.equals(next), "globals changed across batches"); globals=next;
                } else if(text(projection,"name").equals("metadata_full")) {
                    JsonNode next=SaveJson.read(SaveJson.write(tokens(text(projection,"clausewitzTokens"))),JsonNode.class);
                    need(metadata==null || metadata.equals(next), "metadata changed across batches"); metadata=next;
                } else throw new IllegalArgumentException("unexpected raw projection");
            }
            Set<String> observed=new HashSet<>();
            for(JsonNode row:array(raw,"stories")) {
                String id=text(row,"id"); id(id); need(selected.contains(id) && observed.add(id), "raw story selection duplicated/different");
                need(strings(array(row,"path")).equals(List.of("stories","active",id)), "wrong exact Story path");
                Clausewitz.Value value=SaveJson.read(SaveJson.write(row.get("lexemeAst")),Clausewitz.Value.class);
                need(value instanceof Clausewitz.Block, "complete original ordered AST required"); Clausewitz.Block body=(Clausewitz.Block)value;
                need(body.render().equals(text(row,"clausewitzTokens")) && body.render().getBytes(StandardCharsets.UTF_8).length<=RECORD, "raw tokens/AST or byte cap differs");
                Witness witness=new Witness(id,text(row,"producerCanonicalTokenSha256"),FilePins.sha256(SaveJson.write(body)));
                Story story=new Story(id,body,witness), old=stories.putIfAbsent(id,story);
                need(old==null || id.equals(request.observerNativeId()) && old.equals(story), "duplicate/nonimmutable story across batches");
            }
            need(observed.equals(Set.copyOf(selected)), "requested story absent from output");
        }
        need(actor!=null && globals!=null && metadata!=null, "actor/globals/metadata cannot be absent");
        Clausewitz.Value mv=SaveJson.read(SaveJson.write(metadata),Clausewitz.Value.class);
        need(mv instanceof Clausewitz.Block, "metadata AST required"); Clausewitz.Block mb=(Clausewitz.Block)mv;
        need(atom(mb,"version").equals("1.21.0") && atom(mb,"save_game_version").equals("19"), "numeric layout requires actual Florin19 metadata");
        return new Snapshot(checkpoint.offset(),date,actor,globals,stories);
    }

    static Chain interpret(Binding binding,List<Snapshot> snapshots) throws IOException {
        need(snapshots.stream().map(Snapshot::offset).toList().equals(List.of(0,30,395)), "fixed original checkpoints required");
        Snapshot origin=snapshots.getFirst(); Story original=story(origin,binding.observerId());
        Map<String,Clausewitz.Block> ov=variables(original.ast());
        long day=number(ov,"xfma_start_day"), date=number(ov,"xfma_start_date");
        need(day>=0 && day<=1_000_000_000L-395,"original financial day must leave the complete bounded395-day window");
        need(origin.nativeDateRaw()>0 && origin.nativeDateRaw()<=Integer.MAX_VALUE-395L*24,
                "positive int32 Native origin must leave the complete395-day window");
        String account=reference(ov,"xfma_account","story"),coin=reference(ov,"xfma_coin","story");
        String originalHolder=reference(ov,"xfma_holder_before","char");
        need(number(variables(story(origin,account).ast()),"xfm_account_id")==Long.parseLong(binding.observer().targets().accountId())
                && atom(story(origin,account).ast(),"story_cycle").equals("xfm_finance_account")
                && reference(variables(story(origin,account).ast()),"xfm_holder","char").equals(originalHolder), "D0 actual target account/holder identity differs");
        need(number(variables(story(origin,coin).ast()),"xfm_coin_id")==Long.parseLong(binding.observer().targets().coinId())
                && atom(story(origin,coin).ast(),"story_cycle").equals("xfm_finance_coin"), "D0 actual target coin identity differs");
        Story exchange=story(origin,binding.exchangeId()); Map<String,Clausewitz.Block> ev=variables(exchange.ast());
        need(atom(exchange.ast(),"story_cycle").equals("xfm_finance_exchange") && number(ev,"xfm_day")==day && number(ev,"xfm_last_date")==date, "D0 original exchange clock differs");
        List<Day> prefix=List.of(), full=List.of();
        for(Snapshot snapshot:snapshots) {
            int n=snapshot.offset(); need(snapshot.nativeDateRaw()==origin.nativeDateRaw()+24L*n, "Native checkpoint date is not original offset");
            Map<String,Clausewitz.Block> actor=variables(block(snapshot.actor(),"alive_data"));
            String flag="xfma_ai_capacity_e"+binding.observer().observationEpoch();
            need(number(actor,flag+"_armed")==1 && reference(actor,flag+"_story","story").equals(binding.observerId()), "actual actor/epoch observer reference differs");
            need(reference(variableData(snapshot.globals()),"xfm_exchange","story").equals(binding.exchangeId()), "global exchange changed");
            Story observer=story(snapshot,binding.observerId()); Map<String,Clausewitz.Block> vars=variables(observer.ast());
            need(atom(observer.ast(),"story_cycle").equals(flag+"_observer") && atom(observer.ast(),"owner").equals(binding.actorId()), "not this capacity observer/owner");
            need(reference(vars,"xfma_account","story").equals(account) && reference(vars,"xfma_coin","story").equals(coin)
                    && reference(vars,"xfma_holder_before","char").equals(originalHolder), "original watched objects/holder changed");
            for(String bad:List.of("xfma_sample_gap","xfma_bad_target_association","xfma_capacity_record_allocation_failed")) need(!vars.containsKey(bad), "record generation already failed: "+bad);
            need(number(vars,"xfma_ready")==1 && number(vars,"xfma_capacity_protocol")==1 && number(vars,"xfma_start_day")==day && number(vars,"xfma_start_date")==date, "protocol/original D0 changed");
            for(String key:List.of("xfma_capacity_day_records","xfma_daily_samples")) need(number(vars,key)==n, "record/sample denominator differs");
            for(String key:List.of("xfma_capacity_warmup_records")) need(number(vars,key)==Math.min(n,30), "warm denominator differs");
            for(String key:List.of("xfma_capacity_measured_records","xfma_measured_samples")) need(number(vars,key)==Math.max(n-30,0), "measured denominator differs");
            for(String key:List.of("xfma_capacity_skipped_financial_days","xfma_capacity_missing_source_days","xfma_capacity_invalid_work_days")) need(number(vars,key)==0, "permanent source/gap failure");
            for(String key:List.of("xfma_last_sample_day","xfma_capacity_last_record_day","xfma_capacity_last_attempt_day")) need(number(vars,key)==day+n, "original financial frontier differs");
            need(number(vars,"xfma_capacity_last_source_date")==date+n, "source-date frontier differs");
            List<String> ids=listIds(observer.ast(),"xfma_capacity_days"); need(ids.size()==n, "all actual referenced records required");
            Set<String> expected=new HashSet<>(ids); expected.add(binding.observerId());
            if(n==0) { expected.add(account);expected.add(coin);expected.add(binding.exchangeId()); }
            need(snapshot.stories().keySet().equals(expected), "unrelated business records cannot enter capacity samples");
            List<Day> days=new ArrayList<>();
            for(int i=0;i<ids.size();i++) {
                int ordinal=i+1; Story record=story(snapshot,ids.get(i)); Map<String,Clausewitz.Block> r=variables(record.ast());
                need(atom(record.ast(),"story_cycle").equals("xfma_ai_capacity_day_record") && atom(record.ast(),"owner").equals(binding.actorId()), "other business/profile record is not a capacity sample");
                need(reference(r,"xfma_observer","story").equals(binding.observerId()) && reference(r,"xfma_exchange_source","story").equals(binding.exchangeId()), "record source/back-reference differs");
                need(number(r,"xfma_record_protocol")==1 && number(r,"xfma_record_id")==ordinal && number(r,"xfma_window_day")==ordinal, "ordinal/window/protocol differs");
                need(number(r,"xfma_financial_day")==day+ordinal && number(r,"xfma_previous_record_financial_day")==day+ordinal-1
                        && number(r,"xfma_source_script_date")==date+ordinal && number(r,"xfma_previous_source_script_date")==date+ordinal-1, "financial/source-date continuity gap");
                need(number(r,"xfma_skipped_financial_days_before")==0 && number(r,"xfma_measured_sample")== (ordinal>30?1:0)
                        && number(r,"xfma_required_sources_complete")==1, "missing sample/source or warm-measured reclassification");
                Map<String,Observation> sources=new LinkedHashMap<>();
                for(String field:FIELDS) {
                    long available=number(r,"xfma_"+field+"_available"); need(available==0 || available==1, "availability must be exact0/1");
                    String key="xfma_"+field; BigInteger value=available==1?numberBig(r,key):null;
                    need(available==1 || !r.containsKey(key), "unavailable source cannot invent a value");
                    need(!REQUIRED.contains(field) || available==1, "required actual source unavailable: "+field);
                    if(REQUIRED.contains(field) && !field.equals("last_date")) need(value!=null && value.signum()>=0,"negative required source count: "+field);
                    sources.put(field,new Observation(available==1,value));
                }
                BigInteger work=sources.get("ai_work_today").value(),decisions=sources.get("ai_decisions_today").value();
                need(work.signum()>=0 && decisions.signum()>=0 && work.compareTo(decisions)>=0
                        && number(r,"xfma_work_without_decision_available")==1
                        && numberBig(r,"xfma_work_without_decision").equals(work.subtract(decisions)), "actual work/decision consistency differs");
                need(sources.get("last_date").value().equals(BigInteger.valueOf(date+ordinal)), "sample not sourced from this settled script day");
                days.add(new Day(ordinal,day+ordinal,date+ordinal,ordinal>30,sources,record.witness()));
            }
            need(days.size()>=prefix.size() && days.subList(0,prefix.size()).equals(prefix), "immutable original record prefix changed");
            prefix=List.copyOf(days); full=prefix;
        }
        need(full.size()==395 && full.stream().filter(Day::measured).count()==365, "full395/30warm/365measured required");
        return new Chain(origin.nativeDateRaw(),day,date,full);
    }

    private static void verifyNativeDays(Request request,long origin,List<Pin> pins) throws IOException {
        JsonNode report=node(request.originalHostReport(),64*1024*1024,pins);
        JsonNode frozen=node(request.frozenArgv(),RAW,pins);
        need(text(report,"pipe").equals(flag(frozen,"--bridge-pipe")), "natural-day evidence crossed frozen run");
        verifyNativeIntervals(report,origin,request.actorNativeId());
    }

    private static void verifyD0OriginReview(Request request,long origin,List<Pin> pins) throws IOException {
        JsonNode review=node(request.originalD0Review(),RAW,pins),awaiting=node(pin(review.get("awaiting")),RAW,pins);
        need(text(awaiting,"product").equals("financial-markets") && text(awaiting,"case").equals("ai-capacity"),"D0 review borrowed another product/case");
        JsonNode snapshot=object(awaiting,"actual_snapshot"); validateFull(snapshot,request.actorNativeId());
        need(integer(snapshot,"date_raw")==origin,"original D0 review/native archive date differs");
    }

    static void verifyNativeIntervals(JsonNode report,long origin,String actor) {
        need(origin>0 && origin<=Integer.MAX_VALUE-395L*24,"positive int32 Native origin must leave the complete395-day window");
        long frontier=origin; int intervals=0; Set<String> ids=new HashSet<>();
        List<JsonNode> steps=array(report,"steps"); need(steps.size()<=2000, "bounded original Host step history required");
        for(JsonNode step:steps) {
            JsonNode plan=step.get("plan"); if(plan==null || !plan.isObject()) continue;
            if(!"advance_day".equals(plan.path("kind").asText())) continue;
            need(integer(plan,"days")==1 && truth(step,"ok") && ids.add(text(step,"id")), "one original successful natural-day intent required");
            JsonNode result=object(step,"result"),before=object(result,"before"),after=object(result,"after");
            need(integer(result,"requested_days")==1 && integer(before,"date_raw")==frontier, "native original-day prefix is discontinuous");
            long next=integer(after,"date_raw"), elapsed=integer(result,"elapsed_hours");
            need(next-frontier==elapsed && elapsed>=0 && elapsed<=24, "native natural interval skipped/rewound hours");
            JsonNode boundary=result.get("event_boundary");need(boundary!=null,"explicit nullable event boundary is required");
            if(truth(result,"requested_interval_complete")) need(elapsed==24 && boundary.isNull(), "completed natural day must be exactly24h");
            else need(boundary.isObject() && elapsed<24, "incomplete interval must preserve its actual event boundary");
            for(JsonNode frame:List.of(before,after)) validateFull(frame,actor);
            need(integer(after,"native_revision")>integer(before,"native_revision"),"natural-day Full must have a later actual Native publication");
            frontier=next; intervals++;
        }
        need(intervals>=395 && intervals<=1200 && frontier==origin+395L*24, "complete actual395-natural-day Host history required; no14/120day substitution");
    }

    private static void validateFull(JsonNode frame,String actor) {
        need(text(frame,"schema").equals("ck3_1210_full_state_v1") && text(frame,"game_version").equals("1.21.0")
                && text(frame,"executable_sha256").equalsIgnoreCase("2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc")
                && text(frame,"adapter_id").equals("ck3-1.21.0-msvc-x64") && text(frame,"source").equals("injected-dll-named-pipe")
                && truth(frame,"map_ready") && truth(frame,"paused") && truth(frame.path("played_character"),"alive")
                && integer(frame.path("played_character"),"character_id")==Long.parseLong(actor)
                && integer(frame,"native_revision")>0,"actual exact Florin Full/actor required; no Core or historical fixture substitute");
    }

    private static Story story(Snapshot snapshot,String id) { Story row=snapshot.stories().get(id); need(row!=null,"actual named story missing: "+id); return row; }
    private static List<Pin> loadedDependencies() throws IOException {
        List<Pin> result=new ArrayList<>();
        for(Class<?> type:List.of(SaveJson.class,JsonNode.class,com.fasterxml.jackson.core.JsonFactory.class,com.fasterxml.jackson.annotation.JsonCreator.class)) {
            Path path;
            try {path=Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();}
            catch(java.net.URISyntaxException|NullPointerException invalid) {throw new IOException("loaded readback dependency unavailable",invalid);}
            need(Files.isRegularFile(path) && Files.size(path)<=RAW,"actual bounded dependency JAR required");result.add(FilePins.pin(path));
        }
        need(new HashSet<>(result).size()==4,"four distinct actual dependency JARs required");return List.copyOf(result);
    }
    static Map<String,Clausewitz.Block> variables(Clausewitz.Block story) { return variableData(block(story,"variables")); }
    private static Map<String,Clausewitz.Block> variableData(Clausewitz.Block variables) {
        Map<String,Clausewitz.Block> result=new LinkedHashMap<>();
        for(Clausewitz.Entry row:block(variables,"data").entries()) {
            need(row.key().isEmpty() && row.value() instanceof Clausewitz.Block,"original variable envelope required");
            Clausewitz.Block variable=(Clausewitz.Block)row.value(); String name=atom(variable,"flag");
            need(result.putIfAbsent(name,block(variable,"data"))==null,"duplicate saved variable: "+name);
        }
        return result;
    }
    private static List<String> listIds(Clausewitz.Block body,String name) {
        List<Clausewitz.Block> found=new ArrayList<>(); named(body,name,found,0); need(found.size()<=1,"duplicate saved list");
        if(found.isEmpty()) return List.of(); List<String> result=new ArrayList<>();
        for(Clausewitz.Entry entry:found.getFirst().named("item")) {
            need(entry.operator().equals("=") && entry.value() instanceof Clausewitz.Block,"typed story list item required");
            Clausewitz.Block data=(Clausewitz.Block)entry.value(); need(atom(data,"type").equals("story"),"list item must remain story type");
            String id=atom(data,"identity"); id(id); result.add(id);
        }
        need(result.size()<=395 && new HashSet<>(result).size()==result.size(),"bounded unique day list required"); return List.copyOf(result);
    }
    private static void named(Clausewitz.Block body,String name,List<Clausewitz.Block> result,int depth) {
        need(depth<=128,"saved AST depth exceeded");
        if(!body.named("name").isEmpty() && atom(body,"name").equals(name)) result.add(body);
        for(Clausewitz.Entry row:body.entries()) if(row.value() instanceof Clausewitz.Block child) named(child,name,result,depth+1);
    }
    private static BigInteger numberBig(Map<String,Clausewitz.Block> vars,String key) {
        Clausewitz.Block data=vars.get(key); need(data!=null,"missing actual numeric source: "+key); return FinancialProjector.exactNumber(data,LAYOUT);
    }
    private static long number(Map<String,Clausewitz.Block> vars,String key) { return numberBig(vars,key).longValueExact(); }
    private static String reference(Map<String,Clausewitz.Block> vars,String key,String type) {
        Clausewitz.Block data=vars.get(key); need(data!=null && atom(data,"type").equals(type),"actual typed reference required: "+key);
        String id=atom(data,"identity"); id(id); return id;
    }
    private static Clausewitz.Block block(Clausewitz.Block body,String key) {
        List<Clausewitz.Entry> rows=body.named(key); need(rows.size()==1 && rows.getFirst().operator().equals("=") && rows.getFirst().value() instanceof Clausewitz.Block,"one assigned block required: "+key);
        return (Clausewitz.Block)rows.getFirst().value();
    }
    private static String atom(Clausewitz.Block body,String key) { return FinancialProjector.unquote(FinancialProjector.atom(body,key).orElseThrow(()->new IllegalArgumentException("missing saved atom: "+key))); }
    private static Clausewitz.Block tokens(String text) {
        need(text.getBytes(StandardCharsets.UTF_8).length<=RECORD,"raw token record too large");
        Clausewitz.Block root=Clausewitz.parse("record = "+text); need(root.entries().size()==1,"one complete existing token record required"); return block(root,"record");
    }
    private static byte[] read(Pin pin,int maximum) throws IOException {
        Path path=Path.of(pin.path()); need(pin.bytes()>0 && pin.bytes()<=maximum && Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS),"bounded regular pinned metadata required");
        FilePins.verify(path,pin); byte[] bytes=Files.readAllBytes(path); FilePins.verify(path,pin); return bytes;
    }
    private static byte[] readAndTrack(Pin pin,int maximum,List<Pin> pins) throws IOException { byte[] raw=read(pin,maximum); if(!pins.contains(pin))pins.add(pin);return raw; }
    private static JsonNode node(Pin pin,int maximum,List<Pin> pins) throws IOException { return SaveJson.read(readAndTrack(pin,maximum,pins),JsonNode.class); }
    private static Pin pin(JsonNode node) throws IOException { need(node!=null,"actual pin missing"); return SaveJson.read(SaveJson.write(node),Pin.class); }
    private static void samePin(JsonNode actual,Pin expected) throws IOException { need(pin(actual).equals(expected),"original metadata pin differs"); }
    private static void content(JsonNode actual,Pin expected) { need(integer(actual,"bytes")==expected.bytes() && text(actual,"sha256").equals(expected.sha256()),"content pin differs"); }
    private static void frozenMember(JsonNode files,Pin expected) { content(files.get(expected.path()),expected); }
    private static String flag(JsonNode frozen,String key) {
        List<String> args=strings(array(frozen,"argv")); int at=args.indexOf(key); need(at>=0 && at+1<args.size() && args.lastIndexOf(key)==at,"one actual frozen flag required: "+key);return args.get(at+1);
    }
    private static List<String> strings(List<JsonNode> nodes) { List<String> result=new ArrayList<>();for(JsonNode node:nodes){need(node.isTextual(),"string array required");result.add(node.textValue());}return List.copyOf(result); }
    private static List<String> ids(List<JsonNode> nodes) { List<String> result=strings(nodes);result.forEach(CapacityWindowReadback::id);need(new HashSet<>(result).size()==result.size(),"duplicate ID");return result; }
    private static void id(String id) { need(id!=null && id.matches("0|[1-9][0-9]{0,9}") && new BigInteger(id).compareTo(BigInteger.valueOf(4294967295L))<0,"canonical valid uint32 native identity required"); }
    private static JsonNode object(JsonNode node,String key) { JsonNode value=node==null?null:node.get(key); need(value!=null && value.isObject(),"object required: "+key);return value; }
    private static List<JsonNode> array(JsonNode node,String key) { JsonNode value=node==null?null:node.get(key);need(value!=null && value.isArray(),"array required: "+key);List<JsonNode> result=new ArrayList<>();value.forEach(result::add);return result; }
    private static String text(JsonNode node,String key) { JsonNode value=node==null?null:node.get(key);need(value!=null && value.isTextual(),"text required: "+key);return value.textValue(); }
    private static long integer(JsonNode node,String key) { JsonNode value=node==null?null:node.get(key);need(value!=null && value.isIntegralNumber() && value.canConvertToLong(),"exact integer required: "+key);return value.longValue(); }
    private static boolean truth(JsonNode node,String key) { JsonNode value=node==null?null:node.get(key);need(value!=null && value.isBoolean(),"literal bool required: "+key);return value.booleanValue(); }
    private static void need(boolean ok,String message) { if(!ok)throw new IllegalArgumentException(message); }
}
