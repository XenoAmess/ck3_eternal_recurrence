package org.xar.ck3.rrf.save;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;
import com.fasterxml.jackson.annotation.JsonValue;
import com.fasterxml.jackson.databind.JsonNode;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import org.xar.ck3.rrf.Contracts;
import org.xar.ck3.rrf.ExpectedSelection;

/** Versioned offline evidence. Native identities and resource lexemes never pass through floating point. */
public final class SaveContracts {
    private SaveContracts() { }
    public record NativeId(String value) {
        public NativeId {
            new org.xar.ck3.save.SaveContracts.NativeId(value);
        }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING) public static NativeId fromJson(JsonNode node) {
            if (node == null || !node.isTextual()) throw new IllegalArgumentException("native ID must be a string");
            return new NativeId(node.textValue());
        }
        @JsonValue public String value() { return value; }
    }
    public record Pin(String path, long bytes, String sha256) {
        public Pin {
            if (path == null || !Path.of(path).isAbsolute() || bytes < 0) throw new IllegalArgumentException("absolute input pin required");
            Contracts.digest(sha256);
        }
    }
    public record Layout(List<String> actorTable, List<String> riteTable, List<String> faithTable, List<String> religionTable) {
        public Layout {
            actorTable = checkedPath(actorTable); riteTable = checkedPath(riteTable); faithTable = checkedPath(faithTable); religionTable = checkedPath(religionTable);
            Contracts.unique(List.of(String.join("/", actorTable), String.join("/", riteTable), String.join("/", faithTable), String.join("/", religionTable)));
        }
    }
    public record Selection(NativeId actorId, List<NativeId> riteIds, List<NativeId> faithIds, List<NativeId> religionIds) {
        public Selection {
            if (actorId == null || actorId.value().equals("0")) throw new IllegalArgumentException("nonzero runtime actor ID required");
            riteIds = checkedIds(riteIds); faithIds = checkedIds(faithIds); religionIds = checkedIds(religionIds);
        }
    }
    @JsonTypeInfo(use = JsonTypeInfo.Id.NAME, property = "type")
    @JsonSubTypes({@JsonSubTypes.Type(value = InspectOnly.class, name = "inspect_only"), @JsonSubTypes.Type(value = FusionSelection.class, name = "fusion_selection"), @JsonSubTypes.Type(value = CancelUnchanged.class, name = "cancel_unchanged")})
    public sealed interface Expectation permits InspectOnly, FusionSelection, CancelUnchanged { }
    public record InspectOnly() implements Expectation { }
    public record FusionSelection(Pin fixtureManifest, Pin preparedProfileInventory, NativeId resultRiteId) implements Expectation {
        public FusionSelection { if (fixtureManifest == null || preparedProfileInventory == null || resultRiteId == null) throw new IllegalArgumentException("pinned fixture, public prepared inventory and actual result Rite required"); }
    }
    /** v3 only. Existing shared selection supplies complete source/House/Dynasty reads without changing v2 layout. */
    public record CancelUnchanged(Pin beforeSave, Pin fixtureManifest, Pin preparedProfileInventory,
                                  org.xar.ck3.save.SaveContracts.Selection inspectionSelection) implements Expectation {
        public CancelUnchanged {
            if (beforeSave == null || fixtureManifest == null || preparedProfileInventory == null || inspectionSelection == null)
                throw new IllegalArgumentException("complete cancellation physical-save/fixture/selection pins required");
            if (!inspectionSelection.metadataRequired() || inspectionSelection.structureCensus() || !inspectionSelection.projections().isEmpty()
                    || inspectionSelection.tables().size() != 6)
                throw new IllegalArgumentException("six explicit required record tables, metadata and no structural substitute required");
            var kinds = java.util.EnumSet.of(org.xar.ck3.save.SaveContracts.ScopeKind.ACTOR, org.xar.ck3.save.SaveContracts.ScopeKind.RITE,
                    org.xar.ck3.save.SaveContracts.ScopeKind.FAITH, org.xar.ck3.save.SaveContracts.ScopeKind.RELIGION,
                    org.xar.ck3.save.SaveContracts.ScopeKind.HOUSE, org.xar.ck3.save.SaveContracts.ScopeKind.DYNASTY);
            for (var table : inspectionSelection.tables()) {
                if (!kinds.remove(table.kind()) || !table.required() || table.ids().isEmpty()) throw new IllegalArgumentException("complete unique required cancellation tables and selected records required");
                if (java.util.Set.of(org.xar.ck3.save.SaveContracts.ScopeKind.ACTOR, org.xar.ck3.save.SaveContracts.ScopeKind.HOUSE,
                        org.xar.ck3.save.SaveContracts.ScopeKind.DYNASTY).contains(table.kind()) && table.ids().size() != 1)
                    throw new IllegalArgumentException("one actual actor/House/Dynasty identity required");
            }
            if (!kinds.isEmpty()) throw new IllegalArgumentException("incomplete cancellation table selection");
        }
    }
    public record Request(int schemaVersion, String machineId, String repository, Pin save, Pin decoder, Layout layout, Selection selection, Expectation expectation) {
        public Request {
            if (schemaVersion != 2 && schemaVersion != 3) throw new IllegalArgumentException("save inspection request version2 or explicit cancellation version3 required");
            if ((schemaVersion == 3) != (expectation instanceof CancelUnchanged)) throw new IllegalArgumentException("cancellation requires version3; original branches require version2");
            if (machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,95}") || repository == null || !Path.of(repository).isAbsolute() || save == null || decoder == null || layout == null || selection == null || expectation == null) throw new IllegalArgumentException("complete pinned save inspection request and explicit expectation required");
            if (expectation instanceof FusionSelection fusion && !selection.riteIds().contains(fusion.resultRiteId())) throw new IllegalArgumentException("actual fusion result Rite must be selected for complete AST inspection");
        }
    }
    public enum ScopeKind { METADATA, ACTOR, RITE, FAITH, RELIGION, HOUSE, DYNASTY }
    public enum Coverage { FULL_RECORD, DIRECT_SCALARS }
    @JsonTypeInfo(use = JsonTypeInfo.Id.NAME, property = "type")
    @JsonSubTypes({@JsonSubTypes.Type(value = Atom.class, name = "atom"), @JsonSubTypes.Type(value = Block.class, name = "block")})
    public sealed interface Value permits Atom, Block { }
    public record Atom(String raw) implements Value {
        public Atom { if (raw == null || raw.isEmpty()) throw new IllegalArgumentException("empty saved atom"); }
    }
    public record Entry(String key, String operator, Value value) {
        public Entry { if (key == null || operator == null || value == null) throw new IllegalArgumentException("incomplete AST entry"); }
    }
    public record Block(List<Entry> entries) implements Value { public Block { entries = List.copyOf(entries); } }
    public record Scope(ScopeKind kind, Coverage coverage, List<String> path, String canonicalTokenSha256, Block ast) {
        public Scope { path = List.copyOf(path); Contracts.digest(canonicalTokenSha256); if (kind == null || coverage == null || ast == null) throw new IllegalArgumentException("complete saved scope required"); }
    }
    public record Inventory(ScopeKind kind, List<String> path, List<NativeId> ids) {
        public Inventory { path = List.copyOf(path); ids = List.copyOf(ids); Contracts.unique(ids.stream().map(NativeId::value).toList()); }
    }
    public record StreamEvidence(String sha256, String bytes, String tokens, String selectedTokenBytes, List<String> rootKeys, List<Entry> rootScalars) {
        public StreamEvidence { Contracts.digest(sha256); rootKeys = List.copyOf(rootKeys); rootScalars = List.copyOf(rootScalars); }
    }
    @JsonTypeInfo(use = JsonTypeInfo.Id.NAME, property = "type")
    @JsonSubTypes({@JsonSubTypes.Type(value = NotAssessed.class, name = "not_assessed"), @JsonSubTypes.Type(value = SelectionVerified.class, name = "fixture_bound_selection_verified"), @JsonSubTypes.Type(value = CancelVerified.class, name = "cancel_persistent_state_verified")})
    public sealed interface Assessment permits NotAssessed, SelectionVerified, CancelVerified { }
    public record NotAssessed() implements Assessment { }
    /** Only saved exact core/origin selection and both source contributions; no GUI, charge or reload claim. */
    public record SelectionVerified(Pin fixtureManifest, Pin fixtureRequest, Pin preparedProfileInventory,
                                    Pin preparedFixtureRequest, Pin preparedCaseContract, ExpectedSelection expectedSelection,
                                    NativeId resultRiteId, NativeId sourceARiteId, NativeId sourceBRiteId) implements Assessment {
        public SelectionVerified {
            if (fixtureManifest == null || fixtureRequest == null || preparedProfileInventory == null || preparedFixtureRequest == null || preparedCaseContract == null || expectedSelection == null || resultRiteId == null || sourceARiteId == null || sourceBRiteId == null) throw new IllegalArgumentException("complete fixture-bound selection evidence required");
        }
    }
    public record StateValue(boolean present, String token) {
        public StateValue { if (token == null || present == token.isEmpty()) throw new IllegalArgumentException("explicit absent/present saved state required"); }
    }
    public record FieldStamp(boolean present, String sha256) {
        public FieldStamp { if (sha256 == null || present == sha256.isEmpty()) throw new IllegalArgumentException("explicit field presence/hash required"); if (present) Contracts.digest(sha256); }
    }
    public record DraftDifference(String category, String name, FieldStamp before, FieldStamp after) {
        public DraftDifference {
            if(!"explicit-empty-draft-list".equals(category)||name==null||!java.util.Set.of("rrf_candidate_tenets","rrf_candidate_doctrines","rrf_selected_tenets","rrf_selected_doctrines","rrf_family_converts").contains(name)
                    ||before==null||after==null||before.equals(after))throw new IllegalArgumentException("explicit known empty draft-list difference required");
        }
    }
    public record CancelActor(NativeId actorId, String piety, NativeId riteId, NativeId faithId, NativeId houseId, NativeId dynastyId,
                              StateValue state, String canonicalActorSha256) {
        public CancelActor {
            java.util.Objects.requireNonNull(actorId);java.util.Objects.requireNonNull(riteId);java.util.Objects.requireNonNull(faithId);java.util.Objects.requireNonNull(houseId);java.util.Objects.requireNonNull(dynastyId);java.util.Objects.requireNonNull(state);
            if(piety==null||!piety.matches("-?(?:0|[1-9][0-9]{0,15})(?:\\.[0-9]{1,8})?")||piety.startsWith("-")&&new java.math.BigDecimal(piety).signum()==0)throw new IllegalArgumentException("exact saved Piety lexeme required");
            Contracts.digest(canonicalActorSha256);
        }
    }
    public record ObjectInventory(ScopeKind kind, List<String> path, List<NativeId> objectIds, List<NativeId> tombstoneIds) {
        public ObjectInventory {
            if(kind!=ScopeKind.RITE&&kind!=ScopeKind.FAITH)throw new IllegalArgumentException("Rite/Faith inventory required");
            path=checkedPath(path); objectIds=List.copyOf(objectIds); tombstoneIds=List.copyOf(tombstoneIds);
            var all=new java.util.HashSet<NativeId>();for(var id:objectIds)if(!all.add(id))throw new IllegalArgumentException("duplicate live object ID");
            for(var id:tombstoneIds)if(!all.add(id))throw new IllegalArgumentException("duplicate/overlapping tombstone ID");
            if(all.size()>200000)throw new IllegalArgumentException("complete native slot cap exceeded");
        }
    }
    public record RecordStamp(ScopeKind kind, NativeId id, String sha256) {
        public RecordStamp {java.util.Objects.requireNonNull(kind);java.util.Objects.requireNonNull(id);Contracts.digest(sha256);}
    }
    public record PhysicalIdentity(String fileKey, long bytes, String modifiedAt) {
        public PhysicalIdentity {if(fileKey==null||fileKey.isBlank()||bytes<0||modifiedAt==null||modifiedAt.isBlank())throw new IllegalArgumentException("complete actual physical identity required");}
    }
    public record CancelSide(Pin save, PhysicalIdentity physical, String streamSha256, String streamBytes, CancelActor actor,
                             List<ObjectInventory> completeInventories, List<RecordStamp> selectedRecords) {
        public CancelSide {
            java.util.Objects.requireNonNull(save);java.util.Objects.requireNonNull(physical);java.util.Objects.requireNonNull(actor);Contracts.digest(streamSha256);
            if(physical.bytes()!=save.bytes()||streamBytes==null||!streamBytes.matches("[1-9][0-9]{0,18}"))throw new IllegalArgumentException("complete Save/stream sizes required");
            completeInventories=List.copyOf(completeInventories); selectedRecords=List.copyOf(selectedRecords);
            if(completeInventories.size()!=2||completeInventories.stream().map(ObjectInventory::kind).distinct().count()!=2)throw new IllegalArgumentException("both complete inventories required");
        }
    }
    /** Scoped snapshot comparison, never GUI/action or absence of an unobserved transient event. */
    public record CancelVerified(Pin fixtureManifest, Pin preparedProfileInventory, Pin decoder, CancelSide before, CancelSide after,
                                 List<DraftDifference> reportedDraftDifferences, boolean noNewObject, String qualificationScope) implements Assessment {
        public CancelVerified {
            java.util.Objects.requireNonNull(fixtureManifest);java.util.Objects.requireNonNull(preparedProfileInventory);java.util.Objects.requireNonNull(decoder);java.util.Objects.requireNonNull(before);java.util.Objects.requireNonNull(after);
            reportedDraftDifferences=List.copyOf(reportedDraftDifferences);
            Contracts.unique(reportedDraftDifferences.stream().map(DraftDifference::name).toList());
            if (!noNewObject||qualificationScope==null||qualificationScope.isBlank()||!before.completeInventories().equals(after.completeInventories())||!before.selectedRecords().equals(after.selectedRecords()))throw new IllegalArgumentException("verified complete source and inventory equality required");
            if(before.physical().fileKey().equals(after.physical().fileKey()))throw new IllegalArgumentException("two distinct physical Save identities required");
            var b=before.actor();var a=after.actor();
            if(!b.actorId().equals(a.actorId())||!b.riteId().equals(a.riteId())||!b.faithId().equals(a.faithId())||!b.houseId().equals(a.houseId())||!b.dynastyId().equals(a.dynastyId())
                    ||!b.state().equals(a.state())||new java.math.BigDecimal(b.piety()).compareTo(new java.math.BigDecimal(a.piety()))!=0||b.state().present()&&!b.state().token().equals("idle"))throw new IllegalArgumentException("verified persistent actor equality required");
        }
    }
    public record Report(String schema, String machineId, String observedAtUtc, Request request, int decoderExitCode,
                         String decoderStderr, StreamEvidence stream, List<Inventory> inventories, List<Scope> scopes,
                         List<Pin> producerSources, boolean saveUnchanged, boolean gameStarted, Assessment assessment) {
        public Report {
            if (!(request.schemaVersion() == 3 ? "rrf-save-cancel-inspection-v3" : "rrf-save-inspection-v2").equals(schema) || decoderExitCode != 0 || !saveUnchanged || gameStarted || assessment == null) throw new IllegalArgumentException("incomplete offline evidence");
            if ((request.expectation() instanceof FusionSelection) != (assessment instanceof SelectionVerified)) throw new IllegalArgumentException("saved selection expectation/assessment branch mismatch");
            if (request.expectation() instanceof FusionSelection expected && assessment instanceof SelectionVerified verified
                    && (!expected.fixtureManifest().equals(verified.fixtureManifest()) || !expected.preparedProfileInventory().equals(verified.preparedProfileInventory()) || !expected.resultRiteId().equals(verified.resultRiteId()))) throw new IllegalArgumentException("saved selection expectation/assessment identity mismatch");
            if ((request.expectation() instanceof CancelUnchanged) != (assessment instanceof CancelVerified)) throw new IllegalArgumentException("cancellation expectation/assessment branch mismatch");
            if (request.expectation() instanceof CancelUnchanged expected && assessment instanceof CancelVerified verified
                    && (!expected.beforeSave().equals(verified.before().save()) || !request.save().equals(verified.after().save())
                    || !request.decoder().equals(verified.decoder()) || !expected.fixtureManifest().equals(verified.fixtureManifest())
                    || !expected.preparedProfileInventory().equals(verified.preparedProfileInventory()))) throw new IllegalArgumentException("cancellation report identity mismatch");
            if (request.expectation() instanceof CancelUnchanged expected && assessment instanceof CancelVerified verified) {
                if(!request.machineId().equals(machineId)||!request.selection().actorId().equals(verified.before().actor().actorId()))throw new IllegalArgumentException("cancellation actor/machine crossed request identity");
                if(!verified.after().streamSha256().equals(stream.sha256())||!verified.after().streamBytes().equals(stream.bytes()))throw new IllegalArgumentException("cancellation after-stream evidence crossed report");
                var requiredRecords=new java.util.HashSet<String>();
                for(var table:expected.inspectionSelection().tables())if(table.kind()!=org.xar.ck3.save.SaveContracts.ScopeKind.ACTOR)
                    for(var id:table.ids())requiredRecords.add(table.kind().name()+":"+id.value());
                for(var side:List.of(verified.before(),verified.after())) {
                    var actualRecords=new java.util.HashSet<String>();
                    for(var record:side.selectedRecords())if(!actualRecords.add(record.kind().name()+":"+record.id().value()))throw new IllegalArgumentException("duplicate cancellation source record");
                    if(!actualRecords.equals(requiredRecords))throw new IllegalArgumentException("complete selected cancellation source records required");
                    for(var inventory:side.completeInventories()) {
                        var table=expected.inspectionSelection().tables().stream().filter(t->t.kind().name().equals(inventory.kind().name())).findFirst().orElseThrow();
                        if(!table.path().equals(inventory.path())||!inventory.objectIds().containsAll(table.ids().stream().map(n->new NativeId(n.value())).toList()))throw new IllegalArgumentException("complete cancellation inventory must contain actual selected sources");
                    }
                    for(var table:expected.inspectionSelection().tables()) {
                        if(table.kind()==org.xar.ck3.save.SaveContracts.ScopeKind.HOUSE&&!table.ids().getFirst().value().equals(side.actor().houseId().value())
                                ||table.kind()==org.xar.ck3.save.SaveContracts.ScopeKind.DYNASTY&&!table.ids().getFirst().value().equals(side.actor().dynastyId().value()))throw new IllegalArgumentException("cancellation House/Dynasty crossed request identity");
                    }
                }
                for(var inventory:verified.after().completeInventories()) {
                    var observed=inventories.stream().filter(i->i.kind()==inventory.kind()&&i.path().equals(inventory.path())).toList();
                    if(observed.size()!=1||!java.util.Set.copyOf(observed.getFirst().ids()).equals(java.util.Set.copyOf(inventory.objectIds())))throw new IllegalArgumentException("complete cancellation live inventory differs from observed report inventory");
                }
                for(var record:verified.after().selectedRecords()) {
                    var actual=scopes.stream().filter(s->s.kind()==record.kind()&&s.coverage()==Coverage.FULL_RECORD&&s.path().getLast().equals(record.id().value())).toList();
                    if(actual.size()!=1||!actual.getFirst().canonicalTokenSha256().equals(record.sha256()))throw new IllegalArgumentException("cancellation source stamp differs from complete report scope");
                }
                var actualActor=scopes.stream().filter(s->s.kind()==ScopeKind.ACTOR&&s.coverage()==Coverage.FULL_RECORD&&s.path().getLast().equals(request.selection().actorId().value())).toList();
                if(actualActor.size()!=1||!actualActor.getFirst().canonicalTokenSha256().equals(verified.after().actor().canonicalActorSha256()))throw new IllegalArgumentException("cancellation actor stamp differs from complete report scope");
            }
            Instant.parse(observedAtUtc); inventories = List.copyOf(inventories); scopes = List.copyOf(scopes); producerSources = List.copyOf(producerSources);
        }
    }
    private static List<String> checkedPath(List<String> path) {
        List<String> result = List.copyOf(path);
        if (result.isEmpty() || result.size() > 4 || result.stream().anyMatch(p -> !p.matches("[A-Za-z_][A-Za-z0-9_]*"))) throw new IllegalArgumentException("explicit save table path required");
        return result;
    }
    private static List<NativeId> checkedIds(List<NativeId> ids) {
        List<NativeId> result = List.copyOf(ids); if (result.size() > 128) throw new IllegalArgumentException("selected ID cap exceeded");
        Contracts.unique(result.stream().map(NativeId::value).toList()); return result;
    }
}
