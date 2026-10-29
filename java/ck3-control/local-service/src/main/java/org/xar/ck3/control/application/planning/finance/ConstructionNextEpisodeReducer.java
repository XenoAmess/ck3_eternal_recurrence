package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;

/** One transform for actual NEXT and FIRST restore. Saved originals never authorize a current physical Game. */
public final class ConstructionNextEpisodeReducer {
    public static final String FIELD = "java_episode_initialization_construction_v2";
    public enum Origin { NEXT, RESTORED_FIRST }
    public enum Qualification { CURRENT_PROJECTS_OBSERVED, CURRENT_PROJECTS_UNAVAILABLE }
    public sealed interface CurrentProjects permits ObservedProjects, ProjectsUnavailable { Obj toJson(); }
    public record ObservedProjects(ExactRef originalReceipt, Obj finalizedQuery) implements CurrentProjects {
        public ObservedProjects { Objects.requireNonNull(originalReceipt); Objects.requireNonNull(finalizedQuery);
            require(new Text("material_source").equals(finalizedQuery.get("status")), "NEXT project observation requires actual material-query output"); }
        @Override public Obj toJson() { return obj("status", new Text("observed"), "original_read_receipt", ref(originalReceipt),
                "material_query", finalizedQuery, "observation_only", new Bool(true)); }
    }
    public record ProjectsUnavailable(String reason, Optional<ExactRef> originalReceipt) implements CurrentProjects {
        public ProjectsUnavailable { StrictJson.text(reason); Objects.requireNonNull(originalReceipt); }
        @Override public Obj toJson() { return obj("status", new Text("unavailable"), "reason", new Text(reason),
                "original_read_receipt", originalReceipt.<Value>map(ConstructionNextEpisodeReducer::ref).orElse(Nil.INSTANCE)); }
    }
    public record Initialization(Optional<ConstructionDomainLifecycle.Publication> publication, DomainBodies.BodyRef body,
            Qualification qualification) {
        public Initialization { Objects.requireNonNull(publication); Objects.requireNonNull(body); Objects.requireNonNull(qualification); }
    }
    public record Basis(Origin origin, SessionIdentity beforeOwner, SessionIdentity savedOwner, SessionIdentity afterOwner, G2Source source,
            CheckpointPair.FileWitness baselineMaterial, ExactRef baselineEvent, long baselineSequence, String baselineDigest,
            long initializationSequence, String initializationDigest, DomainBodies.BodyRef originalBody,
            ExactRef predecessorDriver, ExactRef firstSavedDriver, SemanticEvidence savedSemantic,
            ExactRef currentDriver, SemanticEvidence currentSemantic) {
        public Basis {
            Objects.requireNonNull(origin); Objects.requireNonNull(beforeOwner); Objects.requireNonNull(savedOwner); Objects.requireNonNull(afterOwner); Objects.requireNonNull(source);
            Objects.requireNonNull(baselineMaterial); Objects.requireNonNull(baselineEvent); Objects.requireNonNull(originalBody);
            Objects.requireNonNull(predecessorDriver); Objects.requireNonNull(firstSavedDriver); Objects.requireNonNull(savedSemantic);
            Objects.requireNonNull(currentDriver); Objects.requireNonNull(currentSemantic);
            StrictJson.safe(baselineSequence, 1); org.xar.ck3.control.continuity.writer.WriterContracts.requireDigest(baselineDigest);
            StrictJson.safe(initializationSequence, baselineSequence); org.xar.ck3.control.continuity.writer.WriterContracts.requireDigest(initializationDigest);
            require(beforeOwner.machineId().equals(savedOwner.machineId()) && savedOwner.machineId().equals(afterOwner.machineId())
                    && afterOwner.machineId().equals(source.machineId()) && !beforeOwner.game().equals(savedOwner.game())
                    && !beforeOwner.sessionId().equals(savedOwner.sessionId()) && savedSemantic.frame().machineId().equals(savedOwner.machineId())
                    && savedSemantic.frame().game().equals(savedOwner.game()) && currentSemantic.frame().machineId().equals(afterOwner.machineId())
                    && currentSemantic.frame().game().equals(afterOwner.game()), "original saved and current owners differ from their own semantics");
            if (origin == Origin.NEXT) require(savedOwner.equals(afterOwner) && firstSavedDriver.equals(currentDriver)
                    && savedSemantic.equals(currentSemantic) && baselineSequence == initializationSequence && baselineDigest.equals(initializationDigest),
                    "live NEXT requires its actual first saved material and BASELINE anchor");
            else require(!savedOwner.game().equals(afterOwner.game()) && !savedOwner.sessionId().equals(afterOwner.sessionId())
                    && initializationSequence > baselineSequence, "FIRST restore requires a distinct replacement and later RESTORED anchor");
            require(originalBody.slot() == DomainBodies.Slot.CONSTRUCTION && originalBody.contractSchema().equals(ConstructionLedgerCodec.SCHEMA),
                    "episode construction requires its actual original canonical BodyRef");
        }
        public Obj toJson() {
            return obj("schema", new Text("xar.java.episode-construction-basis/v2"), "origin", new Text(origin.name()),
                    "before_owner", json(OrdinaryCycleTransitions.sessionToJson(beforeOwner)), "saved_owner", json(OrdinaryCycleTransitions.sessionToJson(savedOwner)),
                    "after_owner", json(OrdinaryCycleTransitions.sessionToJson(afterOwner)), "source", object(parse(G2Wire.sourceBytes(source)), "actual source"),
                    "baseline_material_witness", json(CheckpointPairCodec.fileWitnessToJson(baselineMaterial)), "baseline_event", ref(baselineEvent),
                    "baseline_sequence", new IntegerValue(BigInteger.valueOf(baselineSequence)), "baseline_sha256", new Text(baselineDigest),
                    "initialization_sequence", new IntegerValue(BigInteger.valueOf(initializationSequence)), "initialization_sha256", new Text(initializationDigest),
                    "original_body", json(originalBody.toJson()), "predecessor_driver", ref(predecessorDriver), "first_saved_driver", ref(firstSavedDriver),
                    "saved_semantic", json(OrdinaryCycleTransitions.semanticToJson(savedSemantic)), "current_driver", ref(currentDriver),
                    "current_semantic", json(OrdinaryCycleTransitions.semanticToJson(currentSemantic)));
        }
        public static Basis decode(Obj row) {
            Objects.requireNonNull(row);
            require(row.members().keySet().equals(Set.of("schema", "origin", "before_owner", "saved_owner", "after_owner", "source", "baseline_material_witness",
                    "baseline_event", "baseline_sequence", "baseline_sha256", "initialization_sequence", "initialization_sha256", "original_body",
                    "predecessor_driver", "first_saved_driver", "saved_semantic", "current_driver", "current_semantic"))
                    && new Text("xar.java.episode-construction-basis/v2").equals(row.get("schema")), "exact common construction basis v2 fields required");
            return new Basis(Origin.valueOf(text(row.get("origin"), "actual initialization origin")),
                    OrdinaryCycleTransitions.sessionFromJson(node(row.get("before_owner"))), OrdinaryCycleTransitions.sessionFromJson(node(row.get("saved_owner"))),
                    OrdinaryCycleTransitions.sessionFromJson(node(row.get("after_owner"))), G2Wire.source(node(row.get("source"))),
                    CheckpointPairCodec.fileWitnessFromJson(node(row.get("baseline_material_witness"))),
                    ExactRef.fromJson(node(row.get("baseline_event"))), integer(row.get("baseline_sequence"), "actual baseline sequence").longValueExact(),
                    text(row.get("baseline_sha256"), "actual baseline digest"),
                    integer(row.get("initialization_sequence"), "actual initialization sequence").longValueExact(), text(row.get("initialization_sha256"), "actual initialization digest"),
                    DomainBodies.BodyRef.fromJson(node(row.get("original_body"))),
                    ExactRef.fromJson(node(row.get("predecessor_driver"))), ExactRef.fromJson(node(row.get("first_saved_driver"))),
                    OrdinaryCycleTransitions.semanticFromJson(node(row.get("saved_semantic"))), ExactRef.fromJson(node(row.get("current_driver"))),
                    OrdinaryCycleTransitions.semanticFromJson(node(row.get("current_semantic"))));
        }
        public List<ExactRef> evidence() {
            var refs = new java.util.LinkedHashSet<ExactRef>(savedSemantic.references());
            refs.addAll(currentSemantic.references()); refs.add(currentDriver);
            refs.add(baselineMaterial.reference()); refs.add(baselineEvent); refs.add(originalBody.payload());
            refs.addAll(originalBody.producerSources()); refs.add(predecessorDriver); refs.add(firstSavedDriver); refs.add(source.sourceRef());
            return List.copyOf(refs);
        }
    }
    public record Input(ConstructionLedgerCodec.Ledger original, DriverStateSnapshot.Complete predecessor,
            DriverStateSnapshot.Complete firstSaved, Obj actualSavedSnapshot, DriverStateSnapshot.Complete current,
            Obj actualCurrentSnapshot, Basis basis, CurrentProjects currentProjects) {
        public Input { Objects.requireNonNull(original); Objects.requireNonNull(predecessor); Objects.requireNonNull(firstSaved);
            Objects.requireNonNull(actualSavedSnapshot); Objects.requireNonNull(current); Objects.requireNonNull(actualCurrentSnapshot);
            Objects.requireNonNull(basis); Objects.requireNonNull(currentProjects); }
    }
    public record Result(Obj body, Qualification qualification) {
        public Result { Objects.requireNonNull(body); Objects.requireNonNull(qualification); }
    }
    public static Result reduce(Input input) {
        Objects.requireNonNull(input); var basis = input.basis(); var before = input.predecessor().session();
        var saved = input.firstSaved().session(); var after = input.current().session();
        var frame = basis.currentSemantic().frame().frame();
        require(exact(basis.originalBody().payload(), encode(input.original().original()))
                && exact(basis.predecessorDriver(), input.predecessor().encode()) && exact(basis.firstSavedDriver(), input.firstSaved().encode())
                && exact(basis.currentDriver(), input.current().encode()), "construction original body or original/current Driver bytes differ from their retained references");
        require(!before.episodeRunId().equals(saved.episodeRunId()) && saved.episodeRunId().equals(after.episodeRunId())
                && saved.actorId().equals(after.actorId()), "construction must preserve actual NEXT ancestry and restored actor/episode");
        requireSnapshot(input.firstSaved(), basis.savedSemantic(), input.actualSavedSnapshot(), "original saved");
        requireSnapshot(input.current(), basis.currentSemantic(), input.actualCurrentSnapshot(), "current physical");
        require(basis.savedSemantic().frame().frame().identity().dateRaw().equals(frame.identity().dateRaw()),
                "construction initialization cannot credit gameplay after the saved baseline");
        Qualification qualification = Qualification.CURRENT_PROJECTS_UNAVAILABLE;
        if (input.currentProjects() instanceof ObservedProjects observed) {
            Obj source = object(observed.finalizedQuery().get("source_frame"), "actual current project source");
            require(new Text(after.episodeRunId()).equals(source.get("episode_run_id"))
                    && new IntegerValue(after.actorId()).equals(source.get("actor_character_id"))
                    && integer(source.get("date_raw"), "current project date").equals(frame.identity().dateRaw()),
                    "current projects crossed the current physical player/episode/date");
            object(observed.finalizedQuery().get("world"), "actual current project world");
            qualification = Qualification.CURRENT_PROJECTS_OBSERVED;
        }
        Obj audit = basis.toJson().with("before_actor_character_id", new IntegerValue(before.actorId()))
                .with("before_episode_run_id", new Text(before.episodeRunId())).with("after_actor_character_id", new IntegerValue(after.actorId()))
                .with("after_episode_run_id", new Text(after.episodeRunId()))
                .with("current_projects", input.currentProjects().toJson())
                .with("old_projects_rebound", new Bool(false)).with("actions_replayed", new Bool(false))
                .with("game_day_credit", new IntegerValue(BigInteger.ZERO)).with("new_effect_credit", new IntegerValue(BigInteger.ZERO));
        Obj body = input.original().original().with(FIELD, audit);
        ConstructionLedgerCodec.decodeLedger(encode(body));
        return new Result(body, qualification);
    }
    private static void requireSnapshot(DriverStateSnapshot.Complete driver, SemanticEvidence semantic, Obj snapshot, String role) {
        var session = driver.session(); var frame = semantic.frame().frame();
        require(frame.episodeRunId().equals(session.episodeRunId()) && frame.identity().player().equals(session.actorId())
                && text(snapshot.get("episode_run_id"), role + " episode").equals(session.episodeRunId())
                && integer(object(snapshot.get("played_character"), role + " player").get("character_id"), role + " actor").equals(session.actorId())
                && text(snapshot.get("snapshot_id"), role + " snapshot").equals(frame.snapshotId())
                && integer(snapshot.get("revision"), role + " revision").equals(frame.revision())
                && integer(snapshot.get("native_revision"), role + " native revision").equals(frame.identity().nativeRevision())
                && integer(snapshot.get("date_raw"), role + " date").equals(frame.identity().dateRaw()), role + " Driver differs from its own complete semantic snapshot");
        require(bool(snapshot.get("paused"), role + " paused") && bool(snapshot.get("map_ready"), role + " map_ready")
                && bool(object(snapshot.get("played_character"), role + " player").get("alive"), role + " actor alive"), role + " map must remain paused and available");
    }
    private static Obj ref(ExactRef ref) { return json(ref.toJson()); }
    private static com.fasterxml.jackson.databind.JsonNode node(Value value) { return StrictJson.parse(encode(value)); }
    private static boolean exact(ExactRef ref, byte[] bytes) { return ref.bytes() == bytes.length
            && ref.sha256().equals(org.xar.ck3.control.application.action.ActionCodec.sha256(bytes)); }
    private static Obj json(com.fasterxml.jackson.databind.JsonNode value) { return object(parse(StrictJson.canonical(value)), "actual typed original metadata"); }
}
