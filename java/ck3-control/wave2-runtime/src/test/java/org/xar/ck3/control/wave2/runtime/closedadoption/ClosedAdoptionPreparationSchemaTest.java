package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure tests of the same parsers used by preparation import; no native reads, tickets, processes, or source traversal. */
class ClosedAdoptionPreparationSchemaTest {
    private static final Path ROOT = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize()
            .resolve("closed-preparation-contract-only");
    private static final Path REPO = ROOT.resolve("repo"), OUTPUT = ROOT.resolve("output");
    private static final Path PRODUCTION = ROOT.resolve("production/ROOT-CONTINUITY-WINDOW.json");
    private static final String OBSERVED = "2026-10-23T00:00:01Z", REQUEST_OBSERVED = "2026-10-23T00:00:00Z";
    private static ExactRef ref(Path path) { return new ExactRef(path.toString(),17,"a".repeat(64)); }
    private static ObjectNode identity() {
        return new FileStatIdentity(BigInteger.valueOf(17),"18446744073709551615","1720000000000000000").toJson();
    }
    private static ObjectNode object(ObjectNode row, String field) { return (ObjectNode) row.get(field); }
    private static ObjectNode firstSource(ObjectNode row) { return (ObjectNode) row.get("source_roster").get(0); }
    private static byte[] wire(ObjectNode row) { return ClosedAdoptionJson.encode(row); }
    private static void rejectsNote(ObjectNode row) {
        byte[] raw = wire(row);
        assertThrows(ContractViolationException.class,() -> ClosedAdoptionPreparation.parseNote(raw));
    }
    private static void rejectsRoster(ObjectNode row) {
        byte[] raw = wire(row);
        assertThrows(ContractViolationException.class,() -> ClosedAdoptionPreparation.parseRoster(raw));
    }
    private static ObjectNode note() {
        ObjectNode row = StrictJson.object(); row.put("schema",ClosedAdoptionPreparation.NOTE_SCHEMA); row.put("revision",1);
        row.put("status","PENDING_UNSIGNED_NOT_AUTHORIZATION"); row.put("machine_id","synthetic-preparation-contract");
        row.put("observed_at_utc",OBSERVED); row.put("request_observed_at_utc",REQUEST_OBSERVED);
        row.put("repo",REPO.toString()); row.put("output_root",OUTPUT.toString());
        row.set("request_ref",ref(OUTPUT.resolve("adoption-request.json")).toJson());
        row.set("source_roster_ref",ref(OUTPUT.resolve("source-roster-refresh0001.json")).toJson());
        row.set("immutable_predecessor_ref",ref(OUTPUT.resolve("immutable-head240.json")).toJson());
        row.set("actual_production_predecessor_ref",ref(PRODUCTION).toJson());
        row.set("actual_production_predecessor_identity",identity());
        ObjectNode target = row.putObject("actual_production_target"); target.put("canonical_path",PRODUCTION.toString());
        target.set("writer_source_ref",ref(REPO.resolve("original/window_ledger.py")).toJson());
        row.set("event240_preseed_source",ref(PRODUCTION.resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS/00000240.json")).toJson());
        row.set("event240_source_identity",identity());
        row.set("mechanical_source_ref",ref(REPO.resolve("tools/g2_saved_campaign/current_saved_continuity_v1.py")).toJson());
        row.set("cold_owner_source_ref",ref(REPO.resolve("tools/g2_saved_campaign/root_current_saved_campaign_cold_owner_v1.py")).toJson());
        for (String field : List.of("driver_body_reads","save_body_reads","writer_launches","game_launches")) { row.put(field,0); }
        row.put("java_preparation_executed",true);
        for (String field : List.of("invocation_created","review_plan_created","grants_warm_attachment")) { row.put(field,false); }
        return row;
    }
    private static ObjectNode roster() {
        ObjectNode row = StrictJson.object(); row.put("schema",ClosedAdoptionPreparation.ROSTER_SCHEMA); row.put("revision",1);
        row.put("machine_id","synthetic-preparation-contract"); row.put("observed_at_utc",OBSERVED);
        row.set("prior_manifest_ref",ref(REPO.resolve("java/ck3-control/admission-contracts/src/test/resources/closedpartial/original-sources.json")).toJson());
        row.set("business_manifest_ref",ref(REPO.resolve("java/ck3-control/wave2-runtime/src/test/resources/closedadoption/original-business-sources.json")).toJson());
        var sources = row.putArray("source_roster");
        for (int index=0; index<88; index++) {
            ObjectNode source = sources.addObject(); source.set("expected_ref",ref(ROOT.resolve("sources/source_"+index+".json")).toJson());
            source.set("actual_identity",identity()); source.putArray("labels").add("prior/inputs/row_"+index+"/ref"); source.put("status","MATCH");
        }
        row.put("driver_body_reads",0); row.put("save_body_reads",0); return row;
    }
    private static void requiredFields(ObjectNode valid, Consumer<byte[]> parser) {
        List<String> fields = new ArrayList<>(); valid.fieldNames().forEachRemaining(fields::add);
        for (String field : fields) {
            ObjectNode missing = valid.deepCopy(); missing.remove(field);
            byte[] raw = wire(missing);
            assertThrows(ContractViolationException.class,() -> parser.accept(raw),"missing field: "+field);
        }
    }
    @Test void currentNoteAndRosterRoundTripThroughTheActualTypedParsersAndEmitters() {
        assertEquals("xar.closed-adoption-preparation-note/v2",ClosedAdoptionPreparation.NOTE_SCHEMA);
        assertEquals("xar.closed-adoption-preparation-roster/v2",ClosedAdoptionPreparation.ROSTER_SCHEMA);
        var note = ClosedAdoptionPreparation.parseNote(wire(note()));
        var roster = ClosedAdoptionPreparation.parseRoster(wire(roster()));
        assertEquals(note,ClosedAdoptionPreparation.Note.decode(wire(note.toJson())));
        assertEquals(roster,ClosedAdoptionPreparation.SourceRoster.decode(wire(roster.toJson())));
        assertEquals(StrictJson.parse(wire(note())),StrictJson.parse(wire(note.toJson())));
        assertEquals(StrictJson.parse(wire(roster())),StrictJson.parse(wire(roster.toJson())));
        ObjectNode refreshed = note(); refreshed.put("revision",2);
        object(refreshed,"source_roster_ref").put("path",OUTPUT.resolve("source-roster-refresh0002.json").toString());
        var refreshedNote = ClosedAdoptionPreparation.parseNote(wire(refreshed));
        assertEquals(refreshedNote,ClosedAdoptionPreparation.parseNote(wire(refreshedNote.toJson())));
    }
    @Test void everyNoteRosterAndSourceRowFieldIsRequiredAndUnexpectedFieldsAreRejected() {
        requiredFields(note(),ClosedAdoptionPreparation::parseNote);
        requiredFields(roster(),ClosedAdoptionPreparation::parseRoster);
        ObjectNode original = roster(); List<String> fields = new ArrayList<>(); firstSource(original).fieldNames().forEachRemaining(fields::add);
        for (String field : fields) {
            ObjectNode missing = roster(); firstSource(missing).remove(field);
            rejectsRoster(missing);
        }
        ObjectNode extraNote = note(); extraNote.put("approved",true);
        rejectsNote(extraNote);
        ObjectNode extraRoster = roster(); extraRoster.put("SDK_proof_verified",true);
        rejectsRoster(extraRoster);
        ObjectNode extraSource = roster(); firstSource(extraSource).put("trusted",true);
        rejectsRoster(extraSource);
        ObjectNode extraTarget = note(); object(extraTarget,"actual_production_target").put("approved",true);
        rejectsNote(extraTarget);
    }
    @Test void historicalUnversionedAndOlderOrUnknownSchemasCannotBeImported() {
        for (String schema : List.of("xar.closed-adoption-preparation-note/v1","xar.closed-adoption-preparation-note/v3")) {
            ObjectNode old = note(); old.put("schema",schema);
            rejectsNote(old);
        }
        ObjectNode historical = note(); historical.remove("schema"); historical.remove("revision");
        rejectsNote(historical);
        ObjectNode oldRoster = roster(); oldRoster.put("schema","xar.closed-adoption-preparation-roster/v1");
        rejectsRoster(oldRoster);
    }
    @Test void noteCountersFlagsAndRevisionRejectBooleanFloatNullAndWrongBranchValuesAtTheWireBoundary() {
        for (String field : List.of("driver_body_reads","save_body_reads","writer_launches","game_launches","revision")) {
            for (Consumer<ObjectNode> mutation : List.<Consumer<ObjectNode>>of(row -> row.put(field,"revision".equals(field)),
                    row -> row.put(field,"revision".equals(field) ? 1.0 : 0.0),row -> row.putNull(field))) {
                ObjectNode invalid = note(); mutation.accept(invalid);
                if (invalid.get(field).isFloatingPointNumber()) {
                    assertTrue(StrictJson.parse(wire(invalid)).get(field).isFloatingPointNumber(),"wire preserves the float token before runtime rejection");
                }
                rejectsNote(invalid);
            }
        }
        for (String field : List.of("invocation_created","review_plan_created","grants_warm_attachment")) {
            ObjectNode invalid = note(); invalid.put(field,true);
            rejectsNote(invalid); invalid.put(field,0); rejectsNote(invalid);
        }
        ObjectNode incomplete = note(); incomplete.put("java_preparation_executed",false);
        rejectsNote(incomplete);
        incomplete.put("java_preparation_executed",1); rejectsNote(incomplete);
        for (int value : List.of(0,10000)) {
            ObjectNode invalid = note(); invalid.put("revision",value);
            rejectsNote(invalid);
        }
    }
    @Test void notePathsTimeAndIndependentPredecessorIdentityMustAgree() {
        List<Consumer<ObjectNode>> changes = List.of(
                row -> row.put("repo","relative"), row -> row.put("output_root",OUTPUT.resolve("child/..").toString()),
                row -> row.put("status","VERIFIED"), row -> row.put("observed_at_utc","2026-10-22T23:59:59Z"),
                row -> object(row,"request_ref").put("path",OUTPUT.resolve("other.json").toString()),
                row -> object(row,"source_roster_ref").put("path",OUTPUT.resolve("source-roster-refresh0002.json").toString()),
                row -> object(row,"immutable_predecessor_ref").put("sha256","b".repeat(64)),
                row -> object(row,"actual_production_predecessor_identity").put("bytes",18),
                row -> object(row,"actual_production_target").put("canonical_path",OUTPUT.resolve("fixture-canonical/ROOT-CONTINUITY-WINDOW.json").toString()),
                row -> object(row,"event240_preseed_source").put("path",PRODUCTION.resolveSibling("wrong-event.json").toString()),
                row -> object(row,"event240_source_identity").put("file_id",1844674407370955161L),
                row -> object(row,"mechanical_source_ref").put("path",REPO.resolve("other.py").toString()),
                row -> object(row,"cold_owner_source_ref").put("path",REPO.resolve("other.py").toString()));
        for (var change : changes) {
            ObjectNode invalid = note(); change.accept(invalid);
            rejectsNote(invalid);
        }
    }
    @Test void rosterRequiresExactlyEightyEightUniqueBoundedNonPersistenceSources() {
        List<Consumer<ObjectNode>> changes = List.of(
                row -> ((com.fasterxml.jackson.databind.node.ArrayNode)row.get("source_roster")).remove(87),
                row -> ((com.fasterxml.jackson.databind.node.ArrayNode)row.get("source_roster")).add(firstSource(row).deepCopy()),
                row -> object((ObjectNode)row.get("source_roster").get(1),"expected_ref").put("path",object(firstSource(row),"expected_ref").get("path").textValue()),
                row -> object(firstSource(row),"expected_ref").put("bytes",0),
                row -> object(firstSource(row),"expected_ref").put("bytes",2*1024*1024+1),
                row -> object(firstSource(row),"actual_identity").put("bytes",18),
                row -> firstSource(row).put("status","ACK"),
                row -> object(firstSource(row),"expected_ref").put("path",ROOT.resolve("driver-state.json").toString()),
                row -> object(firstSource(row),"expected_ref").put("path",ROOT.resolve("checkpoint.ck3").toString()),
                row -> object(firstSource(row),"expected_ref").put("path",ROOT.resolve("checkpoint.sav").toString()),
                row -> object(firstSource(row),"expected_ref").put("bytes",17.0),
                row -> row.put("driver_body_reads",false), row -> row.put("save_body_reads",0.0));
        for (var change : changes) {
            ObjectNode invalid = roster(); change.accept(invalid);
            rejectsRoster(invalid);
        }
    }
    @Test void rosterLabelsMustBePresentTypedUniqueBoundedAndSourceQualified() {
        for (Consumer<ObjectNode> mutation : List.<Consumer<ObjectNode>>of(
                source -> source.putArray("labels"),source -> source.putArray("labels").add(true),
                source -> source.putArray("labels").add("prior/inputs/head/ref").add("prior/inputs/head/ref"),
                source -> source.putArray("labels").add("untrusted/inputs/head"),source -> source.putArray("labels").add("prior/../escape"),
                source -> { var labels=source.putArray("labels"); for(int index=0;index<9;index++) { labels.add("prior/row_"+index); } })) {
            ObjectNode invalid = roster(); mutation.accept(firstSource(invalid));
            rejectsRoster(invalid);
        }
    }
}
