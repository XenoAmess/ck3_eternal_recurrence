package org.xar.ck3.control.service.root;

import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.service.root.RootApplicationAssembly.EpisodeDomainInitializationProof.Kind;

/** Retained data only. A decoded input cannot mint Core's sealed initialization proof. */
record GovernanceDomainInitializationInput(Kind kind,DomainBodies.BodyRef previous,DomainBodies.BodyRef original,
        CheckpointPair.FileWitness material,CheckpointPair pair,SessionIdentity savedSession,SemanticEvidence savedSemantic,
        SemanticEvidence currentSemantic,ExactRef hosted,SemanticEvidence readSemantic,Optional<ExactRef> sourceProof,
        SessionIdentity before,SessionIdentity after,G2Source source,long initializationSequence,String initializationDigest) {
    static final String SCHEMA="xar.java-governance-domain-initialization/v2";
    GovernanceDomainInitializationInput(Kind kind,DomainBodies.BodyRef previous,DomainBodies.BodyRef original,
            CheckpointPair.FileWitness material,CheckpointPair pair,SessionIdentity savedSession,SemanticEvidence savedSemantic,
            SemanticEvidence currentSemantic,ExactRef hosted,SemanticEvidence readSemantic,ExactRef sourceProof,
            SessionIdentity before,SessionIdentity after,G2Source source,long initializationSequence,String initializationDigest) {
        this(kind,previous,original,material,pair,savedSession,savedSemantic,currentSemantic,hosted,readSemantic,Optional.of(sourceProof),
                before,after,source,initializationSequence,initializationDigest);
    }
    GovernanceDomainInitializationInput {
        Objects.requireNonNull(kind);Objects.requireNonNull(previous);Objects.requireNonNull(original);
        Objects.requireNonNull(material);Objects.requireNonNull(pair);Objects.requireNonNull(savedSession);
        Objects.requireNonNull(savedSemantic);Objects.requireNonNull(currentSemantic);Objects.requireNonNull(hosted);
        Objects.requireNonNull(readSemantic);Objects.requireNonNull(sourceProof);Objects.requireNonNull(before);
        sourceProof.ifPresent(ref->StrictJson.require(ref.bytes()>0,"supplied source proof must reference nonempty original bytes"));
        Objects.requireNonNull(after);Objects.requireNonNull(source);StrictJson.safe(initializationSequence,0);
        WriterContracts.requireDigest(initializationDigest);
        StrictJson.require(previous.slot()==original.slot()&&previous.contractSchema().equals(original.contractSchema())
                &&previous.producerSources().equals(original.producerSources()),"same registered original domain contract required");
        StrictJson.require(before.machineId().equals(after.machineId())&&savedSession.machineId().equals(after.machineId())
                &&source.machineId().equals(after.machineId())&&!before.game().equals(savedSession.game())&&!before.game().equals(after.game()),"initialization crossed actual old/new Game or machine/source");
        requireOwner(savedSession,savedSemantic);requireOwner(after,currentSemantic);requireOwner(after,readSemantic);
        var paired=pair.frame();var savedFrame=savedSemantic.frame();
        StrictJson.require(paired.game().equals(savedFrame.game())&&paired.machineId().equals(savedFrame.machineId())
                &&paired.frame().episodeRunId().equals(savedFrame.frame().episodeRunId())
                &&paired.frame().identity().player().equals(savedFrame.frame().identity().player())
                &&paired.frame().identity().dateRaw().equals(savedFrame.frame().identity().dateRaw())
                &&savedFrame.frame().revision().compareTo(paired.frame().revision())>=0
                &&savedFrame.frame().identity().nativeRevision().compareTo(paired.frame().identity().nativeRevision())>=0,
                "FIRST post-SAVE semantic must retain paired owner/episode/actor/date and actual later revisions");
        var saved=savedSemantic.frame().frame();var current=currentSemantic.frame().frame();var read=readSemantic.frame().frame();
        StrictJson.require(saved.episodeRunId().equals(current.episodeRunId())&&saved.identity().player().equals(current.identity().player())
                &&saved.identity().dateRaw().equals(current.identity().dateRaw()),"restore changes physical identity, not saved episode/actor/date");
        StrictJson.require(current.episodeRunId().equals(read.episodeRunId())&&current.identity().player().equals(read.identity().player())
                &&current.identity().dateRaw().equals(read.identity().dateRaw())
                &&read.identity().nativeRevision().compareTo(current.identity().nativeRevision())>=0&&read.revision().compareTo(current.revision())>=0,
                "HOSTED original must follow the current physical semantic frame");
        if(kind==Kind.NEXT)StrictJson.require(savedSession.equals(after)&&savedSemantic.equals(currentSemantic),
                "NEXT current facts are the actual first-save facts");
        else StrictJson.require(!savedSession.game().equals(after.game()),"RESTORED_FIRST requires its distinct current physical Game");
    }
    private static void requireOwner(SessionIdentity owner,SemanticEvidence semantic) {
        StrictJson.require(owner.machineId().equals(semantic.frame().machineId())&&owner.game().equals(semantic.frame().game()),
                "semantic original crossed its explicit physical owner");
    }
    byte[] encode() {
        var row=StrictJson.object().put("schema",SCHEMA).put("kind",kind.name());
        row.set("previous",previous.toJson());row.set("original",original.toJson());
        row.set("material_witness",CheckpointPairCodec.fileWitnessToJson(material));row.set("pair",StrictJson.parse(CheckpointPairCodec.encode(pair)));
        row.set("saved_session",OrdinaryCycleTransitions.sessionToJson(savedSession));row.set("saved_semantic",OpeningCheckpointInput.semanticToJson(savedSemantic));
        row.set("current_semantic",OpeningCheckpointInput.semanticToJson(currentSemantic));row.set("hosted_original",hosted.toJson());
        row.set("read_semantic",OpeningCheckpointInput.semanticToJson(readSemantic));row.set("source_proof",ExactRef.optionalToJson(sourceProof));
        row.set("before_session",OrdinaryCycleTransitions.sessionToJson(before));row.set("after_session",OrdinaryCycleTransitions.sessionToJson(after));
        row.set("source",ProposalLifecycleCodec.source(source));row.put("initialization_sequence",initializationSequence);row.put("initialization_digest",initializationDigest);
        return StrictJson.canonical(row);
    }
    static GovernanceDomainInitializationInput decode(byte[] raw) {
        var row=StrictJson.object(StrictJson.parse(raw),Set.of("schema","kind","previous","original","material_witness","pair","saved_session","saved_semantic",
                "current_semantic","hosted_original","read_semantic","before_session","after_session","source","initialization_sequence","initialization_digest"),Set.of("source_proof"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact dual-origin governance producer schema required");
        return new GovernanceDomainInitializationInput(Kind.valueOf(StrictJson.text(row.get("kind"))),DomainBodies.BodyRef.fromJson(row.get("previous")),
                DomainBodies.BodyRef.fromJson(row.get("original")),CheckpointPairCodec.fileWitnessFromJson(row.get("material_witness")),
                CheckpointPairCodec.decode(StrictJson.canonical(row.get("pair"))),OrdinaryCycleTransitions.sessionFromJson(row.get("saved_session")),
                OpeningCheckpointInput.semanticFromJson(row.get("saved_semantic")),OpeningCheckpointInput.semanticFromJson(row.get("current_semantic")),
                ExactRef.fromJson(row.get("hosted_original")),OpeningCheckpointInput.semanticFromJson(row.get("read_semantic")),ExactRef.optionalFromJson(row.get("source_proof")),
                OrdinaryCycleTransitions.sessionFromJson(row.get("before_session")),OrdinaryCycleTransitions.sessionFromJson(row.get("after_session")),G2Wire.source(row.get("source")),
                StrictJson.integer(row.get("initialization_sequence"),0,StrictJson.MAX_SAFE_INTEGER),StrictJson.text(row.get("initialization_digest")));
    }
}
