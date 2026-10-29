package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.contracts.StrictJson.require;
import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.planning.finance.ConstructionLedgerCodec;
import org.xar.ck3.control.application.planning.finance.ConstructionNextEpisodeReducer;
import org.xar.ck3.control.application.planning.finance.ConstructionSavedBody;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.StrictJson;

/** Assertion-only adapter for the actual Core chain fixture. It cannot initialize a domain, mint a proof or grant admission. */
public final class ConstructionRootEpisodeAssertions implements RootEpisodeChainFixture.Assertions {
    private RootEpisodeChainFixture.BeforeImports before;
    private ConstructionSavedBody.Saved original;
    private DomainBodies.BodyRef imported;
    @Override public void beforeDomainImports(RootEpisodeChainFixture.BeforeImports actual) throws IOException {
        require(before == null, "one actual construction assertion scope cannot be replayed");
        var proof = actual.nextProof(); proof.requireCurrent(actual.sameWriter(), actual.context());
        var material = proof.baselineMaterial();
        var old = proof.oldDomain(DomainBodies.Slot.CONSTRUCTION);
        var head = actual.sameWriter().requireHistoricalState(material.originalHeadSequence(), material.originalHeadDigest());
        original = ConstructionSavedBody.read(actual.sameWriter(), head, old.producerSources());
        require(original.reference().equals(old), "fixture original construction BodyRef/native FileID differs from private FIRST custody");
        original.requireUnchanged(actual.sameWriter()); before = actual;
    }
    @Override public void afterDomainImports(RootEpisodeChainFixture.Imported actual) throws IOException {
        require(actual.before() == before && original != null && imported == null, "construction assertion lost its actual before/import pair");
        var same = actual.sameWriter(); var proof = actual.nextProof(); proof.requireCurrent(same, actual.context());
        var body = same.readDomain(DomainBodies.Slot.CONSTRUCTION);
        require(body instanceof DomainBodies.Available, "actual Core did not import the real construction body");
        var known = (DomainBodies.Available) body;
        require(actual.bodies().stream().filter(value -> value.slot() == DomainBodies.Slot.CONSTRUCTION).toList().equals(java.util.List.of(known.reference())),
                "actual returned construction BodyRef is not the same canonical import");
        var ledger = ConstructionLedgerCodec.decodeLedger(known.canonicalBody());
        for (var entry : original.ledger().original().members().entrySet()) if (!entry.getKey().equals(ConstructionNextEpisodeReducer.FIELD))
            require(Objects.equals(entry.getValue(), ledger.original().get(entry.getKey())), "actual construction import changed original full state: " + entry.getKey());
        Obj audit = object(ledger.original().get(ConstructionNextEpisodeReducer.FIELD), "actual construction initialization audit");
        require(new Text(proof.kind().name()).equals(audit.get("origin"))
                && json(original.reference().toJson()).equals(audit.get("original_body"))
                && json(CheckpointPairCodec.fileWitnessToJson(proof.baselineMaterial().witness())).equals(audit.get("baseline_material_witness"))
                && json(OrdinaryCycleTransitions.sessionToJson(proof.baselineMaterial().session())).equals(audit.get("saved_owner"))
                && json(OrdinaryCycleTransitions.sessionToJson(proof.afterSession())).equals(audit.get("after_owner"))
                && json(OrdinaryCycleTransitions.semanticToJson(proof.savedSemantic())).equals(audit.get("saved_semantic"))
                && json(OrdinaryCycleTransitions.semanticToJson(proof.currentSemantic())).equals(audit.get("current_semantic"))
                && integer(audit.get("initialization_sequence"), "actual initialization sequence").longValueExact() == proof.initializationHeadSequence()
                && new Text(proof.initializationHeadDigest()).equals(audit.get("initialization_sha256"))
                && new Bool(false).equals(audit.get("old_projects_rebound")) && new Bool(false).equals(audit.get("actions_replayed")),
                "actual construction producer did not preserve its real saved/current source and no-replay audit");
        Obj projects = object(audit.get("current_projects"), "actual current project qualification");
        require(java.util.Set.of(new Text("observed"), new Text("unavailable")).contains(projects.get("status")), "actual construction qualification is unrecognized");
        if (new Text("unavailable").equals(projects.get("status"))) require(!projects.members().containsKey("material_query"), "unavailable projects cannot become an empty observed world");
        original.requireUnchanged(same); proof.requireCurrent(same, actual.context()); imported = known.reference();
    }
    @Override public void afterPublication(RootEpisodeChainFixture.Published actual) throws IOException {
        require(actual.imported().before() == before && imported != null && actual.session().hasInstalledHost(), "construction fixture publication is not the actual same-Core successor");
        var body = actual.sameWriter().readDomain(DomainBodies.Slot.CONSTRUCTION);
        require(body instanceof DomainBodies.Available known && known.reference().equals(imported), "publication changed the actual imported construction BodyRef");
        original.requireUnchanged(actual.sameWriter());
    }
    private static Obj json(com.fasterxml.jackson.databind.JsonNode value) { return object(parse(StrictJson.canonical(value)), "actual typed construction provenance"); }
}
