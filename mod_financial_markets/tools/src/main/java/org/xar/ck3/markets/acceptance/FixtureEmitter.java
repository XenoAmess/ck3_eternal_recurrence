package org.xar.ck3.markets.acceptance;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.MapperFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.HashSet;
import org.xar.ck3.markets.acceptance.AcceptanceContracts.Content;
import org.xar.ck3.markets.acceptance.AcceptanceContracts.Manifest;
import org.xar.ck3.markets.acceptance.AcceptanceContracts.Pin;
import org.xar.ck3.markets.acceptance.AcceptanceContracts.Request;
import org.xar.ck3.save.Clausewitz;

/** Emits the shared prebuilt-fixture contract. Owns no host, engine identity or business dispatch. */
public final class FixtureEmitter {
    private FixtureEmitter() { }
    static final JsonMapper JSON = JsonMapper.builder(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build()).disable(MapperFeature.ALLOW_COERCION_OF_SCALARS)
            .disable(DeserializationFeature.ACCEPT_FLOAT_AS_INT).enable(DeserializationFeature.FAIL_ON_NULL_FOR_PRIMITIVES)
            .enable(DeserializationFeature.FAIL_ON_NUMBERS_FOR_ENUMS).build();
    static final String CONTROLLED_LOAD_RULES = "common/game_rules/xfm_market_rules.txt";
    private static final String SOURCE = "mod_financial_markets/tools/src/main/java/org/xar/ck3/markets/acceptance/";
    private static final List<String> PRODUCERS = List.of("AcceptanceContracts.java", "ObservationScripts.java", "FixtureEmitter.java", "AcceptanceCommand.java", "FollowupContracts.java", "FollowupObservationScripts.java");

    public static AcceptanceContracts.Emission emit(Path repository, Path output, String machineId, Request request) throws IOException {
        return emit(repository, output, machineId, new FollowupContracts.LegacyInput(request));
    }

    public static AcceptanceContracts.Emission emit(Path repository, Path output, String machineId, FollowupContracts.Input input) throws IOException {
        return emit(repository,output,machineId,input,false);
    }

    public static AcceptanceContracts.Emission emitCrisis20Discovery(Path repository, Path output, String machineId, FollowupContracts.Input input) throws IOException {
        if(!(input instanceof FollowupContracts.ControlledCrisis20Request))throw new IllegalArgumentException("discovery requires the exact controlled crisis20 request");
        return emit(repository,output,machineId,input,true);
    }

    private static AcceptanceContracts.Emission emit(Path repository, Path output, String machineId, FollowupContracts.Input input, boolean discoveryOnly) throws IOException {

        java.util.Objects.requireNonNull(input, "fixture input");
        AcceptanceContracts.require(machineId != null && machineId.matches("[A-Za-z0-9][A-Za-z0-9_-]{1,99}"), "explicit machine identity required");
        Path repo = repository.toRealPath();
        Path destination = output.toAbsolutePath().normalize();
        Path manifestPath = Path.of(destination + ".fixture.json");
        AcceptanceContracts.require(!destination.startsWith(repo) && !repo.startsWith(destination), "fixture output must remain outside repository");
        AcceptanceContracts.require(!Files.exists(destination, LinkOption.NOFOLLOW_LINKS) && !Files.exists(manifestPath, LinkOption.NOFOLLOW_LINKS), "unused fixture and manifest paths required");
        Path parent = destination.getParent();
        AcceptanceContracts.require(parent != null && Files.isDirectory(parent), "existing external output parent required");
        AcceptanceContracts.require(!destination.getFileName().toString().equals(".") && !parent.toRealPath().startsWith(repo), "output parent resolves inside repository");
        List<Pin> producerPins = new ArrayList<>();
        for (String source : PRODUCERS) {
            Path actual = repo.resolve(SOURCE).resolve(source).toRealPath();
            byte[] bytes = Files.readAllBytes(actual);
            try (var packaged = FixtureEmitter.class.getResourceAsStream("/producer-source/org/xar/ck3/markets/acceptance/" + source)) {
                if (packaged == null || !Arrays.equals(bytes, packaged.readAllBytes())) throw new IOException("loaded producer source differs: " + source);
            }
            producerPins.add(pin(actual));
        }
        if(input instanceof FollowupContracts.ControlledFuturesRiskRequest) {
            // Require this actual packaged component, not a historical default/App17 emitter.
            String component="ControlledFuturesRiskFixture.java";
            Path actual=repo.resolve(SOURCE).resolve(component).toRealPath();byte[] bytes=Files.readAllBytes(actual);
            try(var packaged=FixtureEmitter.class.getResourceAsStream("/producer-source/org/xar/ck3/markets/acceptance/"+component)) {
                if(packaged==null||!Arrays.equals(bytes,packaged.readAllBytes()))throw new IOException("loaded risk producer differs");
            }
            producerPins.add(pin(actual));
            for(String source:List.of("common/scripted_effects/xfm_oracle_indexes.txt","common/script_values/xfm_oracle_index_values.txt",
                    "common/scripted_effects/xfm_futures_match.txt","common/script_values/xfm_futures_values.txt")) {
                Path selected=repo.resolve("mod_financial_markets").resolve(source).toRealPath();
                if(!selected.startsWith(repo)||Files.size(selected)>1048576)throw new IOException("bounded risk source required");
                producerPins.add(pin(selected));
            }
        }
        Map<String, byte[]> payloads;
        byte[] requestBytes;
        String caseId;
        List<String> markers;
        if (input instanceof FollowupContracts.LegacyInput legacy) {
            payloads = new LinkedHashMap<>(ObservationScripts.render(legacy.request()));
            requestBytes = JSON.writeValueAsBytes(legacy.request());
            caseId = "core";
            markers = ObservationScripts.MARKERS;
        } else if (input instanceof FollowupContracts.Request followup) {
            payloads = new LinkedHashMap<>(FollowupObservationScripts.render(followup));
            requestBytes = JSON.writeValueAsBytes(followup);
            caseId = followup.caseId().wire();
            markers = followup.markers();
        } else if(input instanceof FollowupContracts.ControlledFuturesRiskRequest risk) {
            payloads=new LinkedHashMap<>(FollowupObservationScripts.renderControlledFuturesRisk(risk));
            requestBytes=JSON.writeValueAsBytes(risk);caseId=risk.caseId();markers=risk.markers();
        } else if (input instanceof FollowupContracts.ControlledFundingRequest funding) {
            payloads = new LinkedHashMap<>(FollowupObservationScripts.renderControlledFunding(funding));
            requestBytes = JSON.writeValueAsBytes(funding);
            caseId = funding.caseId();
            markers = funding.markers();
        } else if (input instanceof FollowupContracts.ControlledDebtAidNewsRequest debt) {
            payloads = new LinkedHashMap<>(FollowupObservationScripts.renderControlledDebtAidNews(debt));
            requestBytes = JSON.writeValueAsBytes(debt);
            caseId = debt.caseId();
            markers = debt.markers();
        } else if (input instanceof FollowupContracts.ControlledCrisis20Request crisis) {
            for (String source : List.of("CrisisSceneBranchFixture.java", "ControlledCrisis20Fixture.java")) {
                Path actual=repo.resolve(SOURCE).resolve(source).toRealPath(); byte[] bytes=Files.readAllBytes(actual);
                try(var packaged=FixtureEmitter.class.getResourceAsStream("/producer-source/org/xar/ck3/markets/acceptance/"+source)) {
                    if(packaged==null || !Arrays.equals(bytes,packaged.readAllBytes())) throw new IOException("loaded crisis20 producer differs: "+source);
                }
                producerPins.add(pin(actual));
            }
            Path selector=repo.resolve("mod_financial_markets/common/scripted_effects/xfm_crisis_scenes.txt").toRealPath();
            Path terminal=repo.resolve("mod_financial_markets/common/scripted_effects/xfm_crisis_progression.txt").toRealPath();
            for(Path actual:List.of(selector,terminal)) if(!actual.startsWith(repo) || Files.size(actual)>32768) throw new IOException("bounded exact production crisis source required");
            Pin selected=pin(selector), completed=pin(terminal);
            if(discoveryOnly) {
                Path guards=repo.resolve("mod_financial_markets/common/scripted_triggers/xfm_crisis_triggers.txt").toRealPath();
                Path values=repo.resolve("mod_financial_markets/common/script_values/xfm_debt_values.txt").toRealPath();
                for(Path actual:List.of(guards,values))if(!actual.startsWith(repo)||Files.size(actual)>65536)throw new IOException("bounded discovery predicate source required");
                Pin guardPin=pin(guards),valuePin=pin(values);
                payloads=new LinkedHashMap<>(FollowupObservationScripts.renderControlledCrisis20Discovery(crisis,Files.readString(selector),Files.readString(guards)));
                if(!guardPin.equals(pin(guards))||!valuePin.equals(pin(values)))throw new IOException("discovery predicates changed during emission");
                producerPins.add(guardPin);producerPins.add(valuePin);
                payloads.put("_xfmc20_discovery_mode.json",JSON.writeValueAsBytes(Map.ofEntries(
                    Map.entry("schema","ck3-controlled-crisis20-discovery-v1"),Map.entry("discovery_only",true),Map.entry("read_only_finance",true),
                    Map.entry("private_namespace","xfmc20d_"),Map.entry("maximum_registry_rows",65536),Map.entry("maximum_candidates",52),
                    Map.entry("maximum_typed_references",104),Map.entry("per_role_maximum",2),Map.entry("context_count",20),Map.entry("case_credit",false))));
            } else payloads=new LinkedHashMap<>(FollowupObservationScripts.renderControlledCrisis20(crisis,Files.readString(selector)));
            if(!selected.equals(pin(selector)) || !completed.equals(pin(terminal))) throw new IOException("crisis production source changed during rendering");
            producerPins.add(selected); producerPins.add(completed);
            requestBytes=JSON.writeValueAsBytes(crisis); caseId=crisis.caseId(); markers=crisis.markers();
        } else if (input instanceof FollowupContracts.ControlledLoadRequest load) {
            payloads = new LinkedHashMap<>(FollowupObservationScripts.renderControlledLoad(load));
            Path rules = repo.resolve("mod_financial_markets").resolve(CONTROLLED_LOAD_RULES).toRealPath();
            if (!rules.startsWith(repo) || Files.size(rules) > 65536) throw new IOException("bounded repository rule source required");
            byte[] originalRules = Files.readAllBytes(rules);
            payloads.put(CONTROLLED_LOAD_RULES, controlledLoadRuleDefaults(originalRules));
            Pin ruleSource = new Pin(rules.toString(), originalRules.length, hash(originalRules));
            if (!ruleSource.equals(pin(rules))) throw new IOException("controlled-load rule source changed during derivation");
            producerPins.add(ruleSource);
            requestBytes = JSON.writeValueAsBytes(load); caseId = load.caseId(); markers = load.markers();
        } else throw new IllegalArgumentException("unsupported fixture input");
        payloads.put("_xfma_request.json", requestBytes);
        Map<String, Content> contents = new LinkedHashMap<>();
        Files.createDirectory(destination);
        for (var payload : payloads.entrySet()) {
            Path target = destination.resolve(payload.getKey()); Files.createDirectories(target.getParent());
            Files.write(target, payload.getValue(), StandardOpenOption.CREATE_NEW);
            contents.put(payload.getKey(), new Content(payload.getValue().length, hash(payload.getValue())));
        }
        Manifest manifest = new Manifest("ck3-mod-acceptance-prebuilt-fixture-v1", "financial-markets", caseId, machineId,
                Instant.now().toString(), destination.toString(), producerPins, contents,
                new AcceptanceContracts.Receipt(markers, Map.of(), !discoveryOnly && (input instanceof FollowupContracts.ControlledFuturesRiskRequest || input instanceof FollowupContracts.ControlledFundingRequest || input instanceof FollowupContracts.ControlledDebtAidNewsRequest || input instanceof FollowupContracts.ControlledCrisis20Request || input instanceof FollowupContracts.ControlledLoadRequest)));
        Files.write(manifestPath, JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(manifest), StandardOpenOption.CREATE_NEW);
        return new AcceptanceContracts.Emission(destination.toString(), pin(manifestPath), false, "NOT_RUN");
    }

    /** Source-only default variant; never edits a profile, saved game or live rule. */
    static byte[] controlledLoadRuleDefaults(byte[] original) throws IOException {
        if (original.length == 0 || original.length > 65536) throw new IOException("bounded nonempty rule source required");
        String text = new String(original, StandardCharsets.UTF_8);
        if (!Arrays.equals(original, text.getBytes(StandardCharsets.UTF_8))) throw new IOException("exact UTF-8 rule source required");
        text = controlledLoadDefault(text, "xfm_market_futures", "xfm_futures_enabled", "xfm_futures_disabled");
        text = controlledLoadDefault(text, "xfm_market_ai_issuance", "xfm_ai_issuance_enabled", "xfm_ai_issuance_disabled");
        return text.getBytes(StandardCharsets.UTF_8);
    }

    private static String controlledLoadDefault(String text, String rule, String enabled, String disabled) throws IOException {
        try {
            var definitions = Clausewitz.parse(text).named(rule);
            if (definitions.size() != 1 || !(definitions.getFirst().value() instanceof Clausewitz.Block block))
                throw new IOException("unique rule definition required: " + rule);
            var defaults = block.named("default");
            if (defaults.size() != 1 || !(defaults.getFirst().value() instanceof Clausewitz.Atom atom)
                    || !enabled.equals(atom.token()) || block.named(enabled).size() != 1 || block.named(disabled).size() != 1)
                throw new IOException("original rule default and both options required: " + rule);
        } catch (IllegalArgumentException error) { throw new IOException("invalid original rule source", error); }
        String before = "default = " + enabled;
        int position = text.indexOf(before);
        if (position < 0 || text.indexOf(before, position + before.length()) >= 0)
            throw new IOException("unique exact default bytes required: " + rule);
        return text.substring(0, position) + "default = " + disabled + text.substring(position + before.length());
    }

    public static Request readRequest(Path path) throws IOException {
        var node = JSON.readTree(Files.readAllBytes(path));
        return readCore(node);
    }

    public static FollowupContracts.Input readInput(Path path) throws IOException {
        var node = JSON.readTree(Files.readAllBytes(path));
        if (node == null || !node.isObject()) throw new IOException("fixture input object required");
        integral(node, "schemaVersion");
        int schema = node.get("schemaVersion").intValue();
        if (schema == 1) return new FollowupContracts.LegacyInput(readCore(node));
        if (schema == 3) {
            textual(node, "caseId", false);
            String controlledCase = node.get("caseId").textValue();
            if (ControlledFuturesRiskFixture.CASE_ID.equals(controlledCase)) {
                closed(node,"schemaVersion","caseId","controlledFixtureOnly");
                if(!node.path("controlledFixtureOnly").isBoolean()||!node.path("controlledFixtureOnly").booleanValue())throw new IOException("explicit controlled risk opt-in required");
                return JSON.treeToValue(node,FollowupContracts.ControlledFuturesRiskRequest.class);
            }
            if ("perpetual-funding-engine-fixture".equals(controlledCase)) {
                closed(node, "schemaVersion", "caseId", "controlledFixtureOnly");
                if (!node.get("controlledFixtureOnly").isBoolean()) throw new IOException("explicit Boolean controlled fixture opt-in required");
                return JSON.treeToValue(node, FollowupContracts.ControlledFundingRequest.class);
            }
            if ("debt-aid-news-engine-fixture".equals(controlledCase)) {
                closed(node, "schemaVersion", "caseId", "controlledFixtureOnly", "participants");
                if (!node.get("controlledFixtureOnly").isBoolean()) throw new IOException("explicit Boolean controlled fixture opt-in required");
                var participants = node.get("participants");
                closed(participants, "debtorAccountId", "aidCreditorAccountId", "playerAccountId");
                for (String name : List.of("debtorAccountId", "aidCreditorAccountId", "playerAccountId")) textual(participants, name, false);
                return JSON.treeToValue(node, FollowupContracts.ControlledDebtAidNewsRequest.class);
            }
            if ("crisis-scenes20-engine-fixture".equals(controlledCase)) {
                closed(node,"schemaVersion","caseId","controlledFixtureOnly","playerAccountId","aidCreditorAccountId","scenes","controls");
                if(!node.get("controlledFixtureOnly").isBoolean()) throw new IOException("literal controlled opt-in required");
                textual(node,"playerAccountId",false); textual(node,"aidCreditorAccountId",false);
                var scenes=node.get("scenes"); if(!scenes.isArray() || scenes.size()!=20) throw new IOException("exact twenty roles required");
                for(var scene:scenes) { closed(scene,"sceneId","accountId"); integral(scene,"sceneId"); if(!scene.get("sceneId").canConvertToInt()) throw new IOException("bounded scene integer"); textual(scene,"accountId",false); }
                var controls=node.get("controls"); closed(controls,"childAccountId","inheritedAccountId","assetAccountId","aidAccountId","restructureAccountId");
                for(String field:List.of("childAccountId","inheritedAccountId","assetAccountId","aidAccountId","restructureAccountId")) textual(controls,field,false);
                return JSON.treeToValue(node,FollowupContracts.ControlledCrisis20Request.class);
            }
            if ("synthetic-controlled-load".equals(controlledCase)) {
                closed(node, "schemaVersion", "caseId", "controlledFixtureOnly", "loadCoins");
                if (!node.get("controlledFixtureOnly").isBoolean()) throw new IOException("explicit Boolean synthetic opt-in required");
                var loads = node.get("loadCoins");
                if (!loads.isArray() || loads.size() != 2) throw new IOException("exact two load stages required");
                for (var value : loads) if (!value.isIntegralNumber() || !value.canConvertToInt())
                    throw new IOException("strict integer load stage required");
                return JSON.treeToValue(node, FollowupContracts.ControlledLoadRequest.class);
            }
            throw new IOException("unsupported controlled fixture case");
        }
        if (schema != 2) throw new IOException("unsupported fixture schemaVersion");
        closed(node, "schemaVersion", "caseId", "observationEpoch", "actor", "targets", "coldBaseline", "scaleTier");
        integral(node, "observationEpoch"); textual(node, "caseId", false); textual(node, "scaleTier", true);
        var actor = node.get("actor");
        closed(actor, "mode", "historyId"); textual(actor, "mode", false); textual(actor, "historyId", true);
        var targets = node.get("targets");
        closed(targets, "accountId", "coinId", "contractId", "positionId", "debtId", "newsId", "indexId");
        for (String field : List.of("accountId", "coinId", "contractId", "positionId", "debtId", "newsId", "indexId")) textual(targets, field, !field.equals("accountId"));
        var baseline = node.get("coldBaseline");
        if (!baseline.isNull()) {
            closed(baseline, "day", "account", "coin", "position", "debt"); integral(baseline, "day");
            var account = baseline.get("account");
            closed(account, "freeCents", "reservedCents", "systemAccount", "inheritanceState", "frozen");
            for (String field : List.of("freeCents", "reservedCents", "systemAccount", "inheritanceState", "frozen")) integral(account, field);
            var coin = baseline.get("coin");
            if (!coin.isNull()) {
                closed(coin, "supplyUnits", "listingState", "priceVersion");
                for (String field : List.of("supplyUnits", "listingState", "priceVersion")) integral(coin, field);
            }
            var position = baseline.get("position");
            if (!position.isNull()) {
                closed(position, "lots", "markCents", "status", "createdDay", "settledDay", "longAccountId", "shortAccountId", "longReservationId", "shortReservationId", "longRemainingCents", "shortRemainingCents");
                for (String field : List.of("lots", "markCents", "status", "createdDay", "settledDay", "longReservationId", "shortReservationId", "longRemainingCents", "shortRemainingCents")) integral(position, field);
                textual(position, "longAccountId", false); textual(position, "shortAccountId", false);
            }
            var debt = baseline.get("debt");
            if (!debt.isNull()) {
                closed(debt, "originalCents", "outstandingCents", "winnerUnpaidCents", "fundRecourseCents", "fundPaidCents", "repaidCents", "writtenOffCents", "sourceDay", "sourceKind", "dueDay", "debtorAccountId", "creditorAccountId");
                for (String field : List.of("originalCents", "outstandingCents", "winnerUnpaidCents", "fundRecourseCents", "fundPaidCents", "repaidCents", "writtenOffCents", "sourceDay", "sourceKind", "dueDay")) integral(debt, field);
                textual(debt, "debtorAccountId", false); textual(debt, "creditorAccountId", false);
            }
        }
        return JSON.treeToValue(node, FollowupContracts.Request.class);
    }

    private static Request readCore(JsonNode node) throws IOException {
        if (node == null || !node.isObject() || node.size() != 2 || !node.has("schemaVersion") || !node.has("actorHistoryId")
                || !node.get("schemaVersion").isIntegralNumber() || !node.get("schemaVersion").canConvertToInt()
                || !node.get("actorHistoryId").isTextual()) throw new IOException("strict fixture integer version and textual history key required");
        return JSON.treeToValue(node, Request.class);
    }
    private static void closed(JsonNode node, String... expected) throws IOException {
        if (node == null || !node.isObject()) throw new IOException("fixture object required");
        Set<String> actual = new HashSet<>(); node.fieldNames().forEachRemaining(actual::add);
        if (!actual.equals(Set.of(expected))) throw new IOException("unknown or missing fixture fields");
    }
    private static void integral(JsonNode node, String field) throws IOException {
        if (!node.has(field) || !node.get(field).isIntegralNumber() || !node.get(field).canConvertToLong()) throw new IOException("strict fixture integer required: " + field);
        if ((field.equals("schemaVersion") || field.equals("observationEpoch")) && !node.get(field).canConvertToInt()) throw new IOException("fixture integer exceeds int range");
    }
    private static void textual(JsonNode node, String field, boolean nullable) throws IOException {
        if (!node.has(field) || !(node.get(field).isTextual() || nullable && node.get(field).isNull())) throw new IOException("strict fixture text required: " + field);
    }
    public static Pin pin(Path path) throws IOException {
        Path actual = path.toRealPath(); byte[] bytes = Files.readAllBytes(actual);
        return new Pin(actual.toString(), bytes.length, hash(bytes));
    }
    private static String hash(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
}
