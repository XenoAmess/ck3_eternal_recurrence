package org.xar.ck3.control.wave2.planning.jointintake;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.HexFormat;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.planning.opportunity.ObservedOpportunitySelector;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.governance.heirdiagnostic.HeirCandidateDiagnosticConsumerPort;

final class FormalProposalIntakeTest {
    private record Corpus(Obj metadata, List<Obj> cases) { public Corpus { cases = List.copyOf(cases); } }
    private static Corpus corpus() throws IOException {
        try (var resource = FormalProposalIntakeTest.class.getResourceAsStream("/jointintake/producer-golden-v1.json.gz")) {
            assertNotNull(resource, "actual producer corpus missing: fail, never skip");
            byte[] compressed = resource.readNBytes(65537); assertTrue(compressed.length <= 65536, "compressed corpus bound");
            byte[] raw;
            try (var gzip = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
                raw = gzip.readNBytes(1048577); assertTrue(raw.length <= 1048576, "raw corpus bound");
                assertEquals(-1, gzip.read(), "full validated gzip trailer required");
            }
            ObjectMapper mapper = new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
                    .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
                    .configure(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES, false);
            ObjectNode document;
            try (var parser = mapper.createParser(raw)) {
                JsonNode root = mapper.readTree(parser); assertTrue(root instanceof ObjectNode); document = (ObjectNode) root;
                assertNull(parser.nextToken());
            }
            JsonNode vectors = document.remove("cases"); assertNotNull(vectors); assertTrue(vectors.isArray());
            List<Obj> cases = new ArrayList<>(); for (JsonNode vector : vectors) cases.add(object(parse(mapper.writeValueAsBytes(vector)), "case"));
            return new Corpus(object(parse(mapper.writeValueAsBytes(document)), "metadata"), cases);
        }
    }
    private static Obj input(String name) throws IOException {
        return corpus().cases().stream().filter(row -> new Text(name).equals(row.get("name")))
                .map(row -> object(row.get("input"), "input")).findFirst().orElseThrow();
    }
    private static Obj sources(Obj input) { return object(input.get("sources"), "sources"); }
    private static void rejects(Obj input) { assertThrows(IllegalArgumentException.class, () -> FormalProposalIntake.collectHistoricalV1(encode(input))); }

    @Test void unchangedProducerAndOriginalDispatcherMatchTheCompleteProjection() throws IOException {
        Corpus corpus = corpus(); assertTrue(corpus.cases().size() >= 25);
        assertTrue(integer(corpus.metadata().get("original_tests_run"), "tests").signum() > 0);
        assertEquals(new IntegerValue(BigInteger.ZERO), corpus.metadata().get("original_test_failures"));
        assertEquals(new IntegerValue(BigInteger.ZERO), corpus.metadata().get("original_test_errors"));
        int accepted = 0, rejected = 0;
        for (Obj vector : corpus.cases()) {
            Obj request = object(vector.get("input"), "input"); byte[] raw = encode(request); byte[] original = raw.clone();
            if (new Bool(true).equals(vector.get("accepted"))) {
                Obj actual = object(parse(FormalProposalIntake.collectHistoricalV1(raw)), "result"), expected = object(vector.get("expected"), "expected");
                for (Map.Entry<String, Value> field : expected.members().entrySet()) assertEquals(field.getValue(), actual.get(field.getKey()), text(vector.get("name"), "name") + ":" + field.getKey());
                for (String optional : List.of("war_cash_resource", "producer_family_status", "producer_faction_status", "incomplete_domains"))
                    assertEquals(expected.members().containsKey(optional), actual.members().containsKey(optional), "missingness: " + optional);
                assertEquals(new Bool(true), actual.get("projection_not_original_collection_receipt"));
                assertEquals(new Bool(false), actual.get("resource_reservation_performed"));
                assertEquals(new Bool(false), actual.get("formal_action_ready")); assertEquals(Nil.INSTANCE, actual.get("selected_step"));
                assertEquals(actual.get("analysis"), parse(ObservedOpportunitySelector.select(encode(actual.get("selector_request")))), "existing selector consumer");
                assertEquals(request, parse(encode(request)), "input round trip"); accepted++;
            } else { rejects(request); rejected++; }
            assertArrayEquals(original, raw, "input bytes never mutated");
        }
        assertTrue(accepted >= 18); assertTrue(rejected >= 7);
    }
    @Test void rawFloatingAndBooleanIntegerTokensCannotBecomeValidObservations() throws IOException {
        Obj request = input("three-active-domains"); Obj source = sources(request);
        for (Value invalid : List.of(new DecimalValue("1.0"), new Bool(true), new Text("1"), Nil.INSTANCE)) {
            byte[] raw = encode(request.with("sources", source.with("max_active_wars", invalid)));
            if (invalid instanceof DecimalValue) assertTrue(new String(raw, StandardCharsets.UTF_8).contains("\"max_active_wars\":1.0"), "send actual float token");
            assertThrows(IllegalArgumentException.class, () -> FormalProposalIntake.collectHistoricalV1(raw));
        }
        Obj domains = object(source.get("domains"), "domains"), building = object(domains.get("building"), "building"), query = object(building.get("query"), "query"), candidate = object(query.get("candidate"), "candidate");
        rejects(request.with("sources", source.with("domains", domains.with("building", building.with("query", query.with("candidate", candidate.with("building_type_id", new DecimalValue("701.0"))))))));
    }
    @Test void everyFrameIdentityAndPrivateSourceStatusRemainBinding() throws IOException {
        Obj request = input("three-active-domains"), source = sources(request), frame = object(source.get("frame"), "frame");
        for (String field : List.of("played_character_id", "native_revision", "date_raw", "revision"))
            rejects(request.with("sources", source.with("frame", frame.with(field, new IntegerValue(integer(frame.get(field), field).add(BigInteger.ONE))))));
        for (String field : List.of("snapshot_id", "episode_run_id")) rejects(request.with("sources", source.with("frame", frame.with(field, new Text("other")))));
        for (String field : List.of("read_only", "advertised")) rejects(request.with("sources", source.with(field, new Bool(field.equals("advertised")))));
        rejects(request.with("sources", source.with("frame", frame.with("future", Nil.INSTANCE))));
    }
    @Test void nativeExtensionsAndOpaqueDecimalEvidenceRemainReadable() throws IOException {
        Obj request = input("peace-building-gift"), source = sources(request), domains = object(source.get("domains"), "domains");
        Obj building = object(domains.get("building"), "building"), query = object(building.get("query"), "query"), candidate = object(query.get("candidate"), "candidate");
        Obj changed = request.with("snapshot", object(request.get("snapshot"), "snapshot").with("new_native_extension", new DecimalValue("1.25")))
                .with("sources", source.with("domains", domains.with("building", building.with("query", query.with("candidate", candidate.with("authored_monthly_income_hundredths", new DecimalValue("1.5")))))));
        Obj result = object(parse(FormalProposalIntake.collectHistoricalV1(encode(changed))), "result");
        Obj selector = object(result.get("selector_request"), "selector request");
        assertEquals(new DecimalValue("1.25"), object(selector.get("snapshot"), "snapshot").get("new_native_extension"));
        Obj proposal = object(array(selector.get("proposals"), "proposals").getFirst(), "building proposal");
        assertEquals(new DecimalValue("1.5"), object(proposal.get("evidence"), "evidence").get("authored_monthly_income_hundredths"));
    }
    @Test void sixDomainOrderAndFiveFamilyAlternativesDoNotBecomeReservations() throws IOException {
        Obj result = object(parse(FormalProposalIntake.collectHistoricalV1(encode(input("all-six-domain-order")))), "result");
        assertEquals(new Arr(List.of(new Text("war"), new Text("council"), new Text("building"), new Text("marriage"), new Text("diplomacy"), new Text("lifestyle"))), result.get("collected_domains"));
        assertEquals(10, array(result.get("collected_candidate_ids"), "candidate ids").size());
        assertFalse(result.members().containsKey("reservation")); assertFalse(result.members().containsKey("dispatch"));
        assertEquals(new Bool(false), result.get("resource_reservation_performed"));
    }
    @Test void strictEnvelopeUtf8DuplicateAndByteBoundsAreActualRejectPaths() throws IOException {
        Obj request = input("three-active-domains"); rejects(request.with("unknown", new Bool(true)));
        String raw = new String(encode(request), StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> FormalProposalIntake.collectHistoricalV1((raw + "{}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> FormalProposalIntake.collectHistoricalV1("{\"schema\":\"a\",\"schema\":\"b\"}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> FormalProposalIntake.collectHistoricalV1(new byte[] {(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> FormalProposalIntake.collectHistoricalV1(new byte[131073]));
    }

    @Test void actualJavaHeirDiagnosticFeedsExistingJointFamilyAdapterAndMatchesTheOriginalConsumer() throws Exception {
        byte[] producerRaw = heirDiagnosticResource("producer-golden.json", 98_304);
        JsonNode producer = StrictJson.parse(producerRaw, 98_304);
        JsonNode receipt = StrictJson.parse(heirDiagnosticResource("consumer-golden.json", 65_536), 65_536);
        assertEquals("xar.ck3.heir-diagnostic.actual-java-downstream-consumers.v3", receipt.path("schema").textValue());
        assertEquals(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(producerRaw)),
                StrictJson.text(receipt.get("input_sha256")), "same original producer bytes required across governance and planning");
        assertEquals(3, producer.path("cases").size());
        assertEquals(3, receipt.path("cases").size());
        int selected = 0;
        boolean[] seen = new boolean[3];
        for (JsonNode consumer : receipt.path("cases")) {
            int index = Math.toIntExact(StrictJson.integer(consumer.get("producer_case"), 0, 2));
            assertFalse(seen[index], "each producer case must be consumed once"); seen[index] = true;
            JsonNode source = producer.path("cases").get(index);
            assertEquals(source.path("name"), consumer.path("name"));
            byte[] diagnostic = HeirCandidateDiagnosticConsumerPort.project(StrictJson.canonical(source.path("input")));
            if (!consumer.has("proposal")) { assertTrue(source.path("input").path("choice").isNull()); continue; }
            selected++;
            ObjectNode plan = StrictJson.object();
            plan.put("selected_step", source.path("plan_consumer").path("selected_step").textValue());
            plan.set("family_marriage_choice", source.path("input").path("choice").deepCopy());
            plan.set("family_marriage_legality", source.path("input").path("legality").deepCopy());
            plan.set("family_marriage_private_diagnostic", StrictJson.parse(diagnostic));
            Obj wirePlan = object(parse(StrictJson.canonical(plan)), "actual Java diagnostic family plan");
            IntakeModel.Frame frame = IntakeWire.frame(object(parse(StrictJson.canonical(consumer.path("frame"))), "actual consumer frame"), true);
            byte[] actual = encode(FamilyProposalAdapter.adapt(frame, wirePlan));
            assertArrayEquals(StrictJson.canonical(consumer.path("proposal")), StrictJson.canonical(StrictJson.parse(actual)),
                    "actual Java producer -> existing Java adapter -> actual original Python consumer proposal");
            for (String missing : List.of("family_marriage_choice", "family_marriage_legality", "family_marriage_private_diagnostic")) {
                ObjectNode changed = plan.deepCopy(); changed.remove(missing);
                Obj invalid = object(parse(StrictJson.canonical(changed)), "missing proof plan");
                assertThrows(IllegalArgumentException.class, () -> FamilyProposalAdapter.adapt(frame, invalid));
            }
            Obj proof = object(wirePlan.get("family_marriage_private_diagnostic"), "diagnostic proof");
            for (String field : List.of("native_revision", "date_raw", "selected_candidate_character_id")) {
                Obj invalid = wirePlan.with("family_marriage_private_diagnostic", proof.with(field,
                        new IntegerValue(integer(proof.get(field), field).add(BigInteger.ONE))));
                assertThrows(IllegalArgumentException.class, () -> FamilyProposalAdapter.adapt(frame, invalid));
            }
            Obj episode = wirePlan.with("family_marriage_private_diagnostic", proof.with("episode_run_id", new Text("other")));
            assertThrows(IllegalArgumentException.class, () -> FamilyProposalAdapter.adapt(frame, episode));
        }
        assertEquals(2, selected);
    }

    private static byte[] heirDiagnosticResource(String filename, int maximumBytes) throws IOException {
        String configured = System.getenv("XAR_REPO_ROOT");
        if (configured == null || configured.isBlank()) { configured = System.getProperty("xar.repo"); }
        assertNotNull(configured, "XAR_REPO_ROOT or xar.repo required for the shared actual governance consumer evidence");
        assertFalse(configured.isBlank(), "configured repository root must be explicit");
        Path root = Path.of(configured).toAbsolutePath().normalize();
        Path path = root.resolve("java/ck3-control/wave3-governance/src/test/resources/heirdiagnostic").resolve(filename);
        try (var input = Files.newInputStream(path)) {
            byte[] raw = input.readNBytes(maximumBytes + 1);
            assertTrue(raw.length <= maximumBytes, "bounded actual shared governance resource required");
            return raw;
        }
    }

    /** Test-only conversion of complete pinned v1 vectors, never a production wire alias. */
    private static Obj currentFixture(Obj historical) {
        assertEquals(new Text(FormalProposalIntake.HISTORICAL_REQUEST_SCHEMA), historical.get("schema"));
        Obj source=sources(historical), domains=object(source.get("domains"),"historical domains");
        Value old=domains.get("marriage");
        if(old!=null&&old!=Nil.INSTANCE) {
            Obj marriage=object(old,"historical explicit marriage source");
            Obj original=object(marriage.get("plan"),"actual historical selected plan");
            FamilyProposalPool.Source typed;
            if(marriage.members().containsKey("plans")) {
                List<Value> plans=array(marriage.get("plans"),"actual historical alternatives");
                assertEquals(original,plans.getFirst(),"historical source already names the original first choice");
                List<Value> choices=plans.stream().map(value->object(value,"actual original alternative").get("family_marriage_choice")).toList();
                Value retained=original.get("family_marriage_valued_choices");
                if(retained!=null)assertEquals(new Arr(choices),retained,"do not override an original valued vector");
                else original=original.with("family_marriage_valued_choices",new Arr(choices));
                typed=FamilyProposalPool.collect(original);
            } else typed=new FamilyProposalPool.ExistingBetrothal(original);
            assertEquals(typed,FamilyProposalPool.decodeSource(FamilyProposalPool.encodeSource(typed)));
            domains=domains.with("marriage",FamilyProposalPool.toJson(typed));
        }
        return historical.with("schema",new Text(FormalProposalIntake.REQUEST_SCHEMA)).with("sources",source.with("domains",domains));
    }
    @Test void currentCompactProducerFeedsEveryOriginalAcceptedDomainAndTheActualSelectorWithoutChangingTheOracle() throws IOException {
        int accepted=0;boolean betrothal=false,pool=false;
        for(Obj vector:corpus().cases()) {
            if(!new Bool(true).equals(vector.get("accepted")))continue;
            Obj original=object(vector.get("input"),"original pinned input"),current=currentFixture(original);
            assertThrows(IllegalArgumentException.class,()->FormalProposalIntake.collect(encode(original)),"current never probes historical v1");
            byte[] raw=encode(current);assertTrue(raw.length<=131072);
            assertEquals(current,parse(raw),"full current input survives the same bounded JSON reader");
            assertThrows(IllegalArgumentException.class,()->FormalProposalIntake.collectHistoricalV1(raw),"historical never swallows current v2");
            Obj actual=object(parse(FormalProposalIntake.collect(raw)),"current actual complete intake");
            Obj expected=object(vector.get("expected"),"unaltered original expected");
            for(Map.Entry<String,Value> field:expected.members().entrySet())
                assertEquals(field.getValue(),actual.get(field.getKey()),text(vector.get("name"),"name")+":"+field.getKey());
            assertEquals(actual.get("analysis"),parse(ObservedOpportunitySelector.select(encode(actual.get("selector_request")))));
            Obj domains=object(sources(current).get("domains"),"current domains");
            if(domains.get("marriage") instanceof Obj marriage) {
                String kind=text(marriage.get("kind"),"typed marriage kind");
                if(kind.equals("existing_betrothal"))betrothal=true;else if(kind.equals("valued_first_heir"))pool=true;
                else fail("unknown current typed family source");
                Obj headerOnly=original.with("schema",new Text(FormalProposalIntake.REQUEST_SCHEMA));
                assertThrows(IllegalArgumentException.class,()->FormalProposalIntake.collect(encode(headerOnly)),"new header cannot alias an old nested source");
            }
            accepted++;
        }
        assertTrue(accepted>=18);assertTrue(betrothal,"retain the actual pre-existing betrothal capability");assertTrue(pool,"retain all five actual candidates");
    }
}
