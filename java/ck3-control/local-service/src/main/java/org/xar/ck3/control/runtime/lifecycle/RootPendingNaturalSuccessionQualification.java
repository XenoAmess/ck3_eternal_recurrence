package org.xar.ck3.control.runtime.lifecycle;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.FullSnapshot;
import org.xar.ck3.control.application.lifecycle.LifecycleObservationPort;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification;
import org.xar.ck3.control.application.readiness.NativeSourceProofCodec;
import org.xar.ck3.control.application.readiness.NativeSourceProofDocument;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts.Head;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.Session;
import org.xar.ck3.control.nativebridge.capabilities.family.PrisonerTerminalQueries;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.Frame;
import org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004;
import org.xar.ck3.control.wave2.governance.succession.PendingModalClearance;
import org.xar.ck3.control.wave2.governance.succession.SuccessionModel.Verdict;
import org.xar.ck3.control.wave2.governance.succession.SuccessionNativeEstate12004;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerMaterial12004;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerOptionIntent;
import org.xar.ck3.control.runtime.lifecycle.RootOriginalNaturalSuccessionVerifier.Originals;
import org.xar.ck3.control.runtime.lifecycle.RootOriginalNaturalSuccessionVerifier.Packet;

/**
 * Independent two-stage qualification for the original post-Continue UI order.
 * PendingCause never means final UI clearance, LifecycleApplied, SAVE readiness or replay permission.
 * Neither JSON nor a public constructor can mint PendingCause or Finalized.
 */
public final class RootPendingNaturalSuccessionQualification {
    @FunctionalInterface public interface OriginalReader {
        byte[] readExact(ExactRef reference)throws IOException;
    }
    public record EstateOriginals(PlanningReadReceipt successorRootRead,ExactRef readReference,
            ExactRef resultReference,ExactRef semanticReference,ExactRef originalKnown) {
        public EstateOriginals {Objects.requireNonNull(successorRootRead);for(ExactRef ref:List.of(readReference,resultReference,semanticReference,originalKnown))StrictJson.require(Objects.requireNonNull(ref).bytes()>0,"actual first successor estate and Known originals required");}
    }
    public record CauseOriginals(Originals originals,SuccessionNativeEstate12004.ComparedEstate estate,EstateOriginals estateOriginals) {
        public CauseOriginals {Objects.requireNonNull(originals);Objects.requireNonNull(estate);Objects.requireNonNull(estateOriginals);}
    }
    public interface RootCausePort extends OriginalReader {
        /** Actual private precommit writer/source/clock/actor authority. The original readReference must
         * load the identical first successorRootRead through the sole archive codec. All four estate
         * references must belong to this same retained actual read/full terminal frame, live or historical.
         * Revalidation may query independently but must never replace those original references. */
        CauseOriginals openQualified(ActionCommand parent,LifecycleObservationPort.Snapshot actual,Head head)throws IOException;
        byte[] readExact(ExactRef reference)throws IOException;
        void requireCurrent(CauseOriginals originals,ActionCommand parent,LifecycleObservationPort.Snapshot actual,Head head)throws IOException;
    }
    public record RetainedOriginals(ActionCommand parent,LifecycleObservationPort.Snapshot oldTerminal,
            Head precommitHead,RootCausePort historicalPort) {
        public RetainedOriginals {Objects.requireNonNull(parent);Objects.requireNonNull(oldTerminal);Objects.requireNonNull(precommitHead);Objects.requireNonNull(historicalPort);}
    }
    public interface RootRetainedCausePort {
        /** Actual same writer must rederive exact historical Head/pins/domain and canonical Unknown
         * parent -> pending publication ancestry. Old full Known/native/SEM/clock/estate originals
         * are replayed under the private current source guard, never filled from current new-actor DATA.
         * The returned historical port remains bound to that private writer/thread/source scope. */
        RetainedOriginals openRetainedQualified(ExactRef retainedProof,FullSnapshot current,
                ContinuityStorePort.Session same,SourceQualification source,Head currentHead)throws IOException;
        void requireRetainedCurrent(RetainedOriginals originals,ExactRef retainedProof,PendingCause rederived,
                FullSnapshot current,ContinuityStorePort.Session same,SourceQualification source,Head currentHead)throws IOException;
    }
    /** DATA returned only by the installed Root physical/writer scope; a record cannot issue custody. */
    public enum ContinuityPurpose { PENDING_UI,FINALIZED_METADATA_ONLY }
    public record ContinuityOriginals(ExactRef binding,PendingSameGameContinuity.Binding document,ContinuityPurpose purpose,DriverSnapshotFacts.Known actualKnown) {
        public ContinuityOriginals {finalRef(binding);Objects.requireNonNull(document);Objects.requireNonNull(purpose);Objects.requireNonNull(actualKnown);}
    }
    public interface RootRetainedContinuityPort extends OriginalReader {
        /** Must hold the actual current physical lease and the same writer. Reopen canonical retained
         * archive/pins, full native/Known/SEM and immutable v3 source Witnesses. Preflight the real Rebind
         * reducer under that writer; new binding/current materials are exact prepared archive blobs and
         * must enter the canonical closure in the same Rebind CAS. They need not be committed beforehand.
         * If that exact transport was already rebound, replay the original canonical Rebind reducer and
         * then verify this fresh current frame. Never submit another Rebind or reuse an expired custody.
         * FINALIZED must instead replay its exact original finalizeVerified and any sole Save metadata
         * transition. Return FINALIZED_METADATA_ONLY; it cannot reopen pending UI or any Native action.
         * Neither JSON, a historical source reader nor an old transport token provides this authority. */
        ContinuityOriginals openQualified(PendingCause cause,ExactRef retainedCauseProof,FullSnapshot current,
                ContinuityStorePort.Session same,SourceQualification source,Head head)throws IOException;
        void requireCurrent(ContinuityOriginals originals,PendingCause cause,ExactRef retainedCauseProof,FullSnapshot current,
                ContinuityStorePort.Session same,SourceQualification source,Head head)throws IOException;
        /** For a finalization originally performed after reconnect, reopen its exact canonical binding.
         * This is historical replay under the held current lease, never a fabricated historical lease. */
        ContinuityOriginals openHistoricalFinalQualified(ContinuityOriginals currentContinuity,PendingCause cause,
                ExactRef retainedCauseProof,RetainedFinalizationOriginals historical,FullSnapshot current,
                ContinuityStorePort.Session same,SourceQualification source,Head head)throws IOException;
        void requireHistoricalFinalCurrent(ContinuityOriginals historicalContinuity,ContinuityOriginals currentContinuity,
                PendingCause cause,ExactRef retainedCauseProof,RetainedFinalizationOriginals historical,FullSnapshot current,
                ContinuityStorePort.Session same,SourceQualification source,Head head)throws IOException;
    }
    /** Private capability tied to one real physical/writer scope, not a portable or persisted ticket. */
    public static final class ReconnectedCause {
        private final RootPendingNaturalSuccessionQualification owner;private final PendingCause cause;
        private final RetainedOriginals historical;private final ExactRef retainedProof;private final ContinuityOriginals continuity;
        private final FullSnapshot current;private final ContinuityStorePort.Session same;private final SourceQualification source;private final Head head;
        private ReconnectedCause(RootPendingNaturalSuccessionQualification owner,PendingCause cause,RetainedOriginals historical,
                ExactRef retainedProof,ContinuityOriginals continuity,FullSnapshot current,ContinuityStorePort.Session same,SourceQualification source,Head head) {
            this.owner=owner;this.cause=cause;this.historical=historical;this.retainedProof=retainedProof;this.continuity=continuity;
            this.current=current;this.same=same;this.source=source;this.head=head;
        }
        /** Historical DTO only: the original same-connection APIs remain strict. */
        public PendingCause historicalCause(){return cause;}
        public ExactRef continuityBinding(){return continuity.binding();}
        public String causeDigest(){return cause.causeDigest();}
        public ContinuityPurpose purpose(){return continuity.purpose();}
    }
    public static final class ReconnectedFinalized {
        private final RootPendingNaturalSuccessionQualification owner;private final ReconnectedCause custody;
        private final RetainedFinalized retained;private final Optional<ContinuityOriginals> historicalContinuity;
        private ReconnectedFinalized(RootPendingNaturalSuccessionQualification owner,ReconnectedCause custody,
                RetainedFinalized retained,Optional<ContinuityOriginals> historicalContinuity) {
            this.owner=owner;this.custody=custody;this.retained=retained;this.historicalContinuity=historicalContinuity;
        }
        public byte[] originalProof(){return retained.originalProof();}public String digest(){return retained.digest();}
        public String causeDigest(){return retained.causeDigest();}public RetainedFinalizationOriginals originals(){return retained.originals();}
        public ExactRef retainedProof(){return retained.retainedProof();}public FullSnapshot currentFrame(){return retained.currentFrame();}
        public ExactRef continuityBinding(){return custody.continuityBinding();}public boolean metadataOnly(){return true;}
    }
    /** First live final ROOT read and all seven original Known slots, retained before the business CAS. */
    public record FinalMaterials(PlanningReadReceipt currentRootRead,ExactRef rootReadReference,
            ExactRef originalKnown,ExactRef originalSemantic,DriverSnapshotFacts.Known actualKnown,ExactRef actualObservation) {
        public FinalMaterials {
            Objects.requireNonNull(currentRootRead);Objects.requireNonNull(actualKnown);
            for(ExactRef ref:List.of(rootReadReference,originalKnown,originalSemantic,actualObservation))
                StrictJson.require(Objects.requireNonNull(ref).bytes()>0,"actual final ROOT/Known/SEM originals required");
        }
    }
    public record FinalOriginals(Session session,Frame frame,Packet initialTimeline,Optional<Packet> close,
            List<Packet> postqueries,ExactRef currentRootResult,ExactRef pendingContinueReceipt,
            ExactRef pendingContinueDriver,ExactRef canonicalPublicationProof,Optional<ExactRef> verifiedDateAdvance,
            Optional<Packet> finalTimelineAfterDateAdvance,FinalMaterials materials) {
        public FinalOriginals {
            Objects.requireNonNull(session);Objects.requireNonNull(frame);Objects.requireNonNull(initialTimeline);Objects.requireNonNull(materials);
            Objects.requireNonNull(close);Objects.requireNonNull(verifiedDateAdvance);Objects.requireNonNull(finalTimelineAfterDateAdvance);postqueries=List.copyOf(postqueries);
            StrictJson.require(close.isPresent()==verifiedDateAdvance.isPresent()&&close.isPresent()==finalTimelineAfterDateAdvance.isPresent(),"once-Close requires actual qualified date advance; already-clear cannot invent it");
            verifiedDateAdvance.ifPresent(ref->StrictJson.require(ref.bytes()>0,"nonempty actual date-advance proof required"));
            for(ExactRef ref:List.of(currentRootResult,pendingContinueReceipt,pendingContinueDriver,canonicalPublicationProof))
                StrictJson.require(Objects.requireNonNull(ref).bytes()>0,"nonempty actual final originals required");
            StrictJson.require(close.isPresent()?!postqueries.isEmpty()&&postqueries.size()<=8:postqueries.isEmpty(),
                    "once-Close requires actual one-to-eight postqueries; no-Close has no invented query");
        }
    }
    public interface RootFinalPort {
        /**
         * Verify the sole canonical PendingContinue publication receipt/head/Driver ancestry, exact
         * private cause custody, current source epoch and same physical Game under its actual writer.
         * A pending publication is not a previously final LifecycleApplied receipt. For Close, verify the retained actual Life/clock date-advance
         * receipt and its canonical new-episode writer ancestry; DTO dates alone are insufficient. Cold/reconnection
         * requires a separate actual private rebind contract; this version accepts same connection only.
         */
        FinalOriginals openQualified(PendingCause cause,FullSnapshot current,ContinuityStorePort.Session borrowed,
                SourceQualification source,Head head)throws IOException;
        /** Replay the actual read guards/source/complete SEM/native ancestry; reference-shaped DATA is insufficient. */
        PendingModalClearance.SceneQuery openQualifiedModalQuery(Packet original,ContinuityStorePort.Session same)throws IOException;
        void requireCurrent(PendingCause cause,FullSnapshot current,ContinuityStorePort.Session borrowed,
                SourceQualification source,Head head,FinalOriginals originals)throws IOException;
    }
    /** Only original bytes and genuine archived read guards; this interface cannot issue a Root token. */
    public interface RetainedFinalEvidence extends OriginalReader {
        PendingModalClearance.SceneQuery openQualifiedModalQuery(Packet original,ContinuityStorePort.Session same)throws IOException;
    }
    /** DATA until the Root port replays the sole Save canonical metadata reader for this exact event. */
    public record CanonicalLifecycle(ExactRef canonicalEvent,
            org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof proof) {
        public CanonicalLifecycle {finalRef(canonicalEvent);Objects.requireNonNull(proof);}
    }
    public record RetainedFinalizationOriginals(FullSnapshot beforeFinal,Head beforeFinalHead,
            Optional<ExactRef> originalSourceQualification,FinalOriginals originals,RetainedFinalEvidence evidence,
            ExactRef canonicalFinalizationDomain,Optional<CanonicalLifecycle> canonicalLifecycle) {
        public RetainedFinalizationOriginals {
            Objects.requireNonNull(beforeFinal);Objects.requireNonNull(beforeFinalHead);Objects.requireNonNull(originals);Objects.requireNonNull(evidence);
            Objects.requireNonNull(originalSourceQualification);
            originalSourceQualification.ifPresent(ref->StrictJson.require(ref.bytes()>0,"nonempty actual original source qualification required"));
            finalRef(canonicalFinalizationDomain);Objects.requireNonNull(canonicalLifecycle);
        }
        public RetainedFinalizationOriginals(FullSnapshot beforeFinal,Head beforeFinalHead,
                ExactRef originalSourceQualification,FinalOriginals originals,RetainedFinalEvidence evidence,
                ExactRef canonicalFinalizationDomain,Optional<CanonicalLifecycle> canonicalLifecycle) {
            this(beforeFinal,beforeFinalHead,Optional.of(originalSourceQualification),originals,evidence,canonicalFinalizationDomain,canonicalLifecycle);
        }
    }
    public interface RootRetainedFinalizationPort {
        /** Reopen the exact already-committed FINALIZE import/predecessor Head, beforeKnown/native,
         * original source proof and every final read/control/Life original. The current real physical
         * lease/source guard must prove the sole version+1 post-CAS Known, without subsequent business
         * history. If canonicalLifecycle is present, the sole Save reader must verify the exact
         * SUCCESSOR_PENDING_FINALIZED metadata event/reducer, preserved full Driver/auxiliary and
         * version+2; a decoded Recorded proof or settled-looking receipt alone is insufficient.
         * No replacement query or constructed historical SourceQualification is accepted. */
        RetainedFinalizationOriginals openRetainedQualified(PendingCause cause,ExactRef retainedProof,
                FullSnapshot current,ContinuityStorePort.Session same,SourceQualification actualCurrentSource,Head actualCurrentHead)throws IOException;
        /** Mandatory same private historical scope, actual writer and current physical source replay. */
        void requireRetainedCurrent(RetainedFinalizationOriginals originals,PendingCause cause,ExactRef retainedProof,
                FullSnapshot current,ContinuityStorePort.Session same,SourceQualification actualCurrentSource,Head actualCurrentHead)throws IOException;
    }
    /** Custody of an already-applied historical finalization, usable only for the metadata finish. */
    public static final class RetainedFinalized {
        private final RootPendingNaturalSuccessionQualification owner;private final PendingCause cause;
        private final Finalized finalized;private final RetainedFinalizationOriginals originals;
        private final ExactRef retainedProof;private final FullSnapshot current;private final SourceQualification source;private final Head head;
        private RetainedFinalized(RootPendingNaturalSuccessionQualification owner,PendingCause cause,Finalized finalized,
                RetainedFinalizationOriginals originals,ExactRef retainedProof,FullSnapshot current,SourceQualification source,Head head) {
            this.owner=owner;this.cause=cause;this.finalized=finalized;this.originals=originals;this.retainedProof=retainedProof;this.current=current;this.source=source;this.head=head;
        }
        public byte[] originalProof(){return finalized.originalProof();}public String digest(){return finalized.digest();}
        public String causeDigest(){return cause.causeDigest();}public RetainedFinalizationOriginals originals(){return originals;}
        public ExactRef retainedProof(){return retainedProof;}public FullSnapshot currentFrame(){return current;}
        public boolean metadataOnly(){return true;}
    }
    public enum FinalClearance {
        ALREADY_CLEAR("already_clear"),CLOSED_AND_DATE_ADVANCED("legal_close_then_actual_date_advance_observed_clear");
        private final String wire;FinalClearance(String wire){this.wire=wire;}public String wire(){return wire;}
        private static FinalClearance parse(String wire){for(var value:values())if(value.wire.equals(wire))return value;throw new IllegalArgumentException("actual final modal clearance required");}
    }
    public static final String FINAL_PROOF_SCHEMA="xar.java.post-continue-natural-finalization/v2";
    public static final int FINAL_PROOF_MAX_BYTES=65_536;
    private static final Set<String> FINAL_PROOF_FIELDS=Set.of("schema","machine_id","observed_at_utc","pending_cause_sha256",
            "writer_head_sha256","writer_head_sequence","new_episode_run_id","successor_character_id","modal","date_raw",
            "replay_authorized","business_reapply_authorized","actual_ordinary_snapshot","actual_observation","current_root","current_root_read",
            "original_known","original_semantic","pending_continue_receipt","pending_continue_driver","canonical_publication",
            "initial_timeline","postqueries","close","verified_date_advance","final_timeline_after_date_advance");
    /** Sole strict persisted final-material contract. Decoding this DATA never constructs Finalized. */
    public record FinalProofDocument(String machineId,Instant observedAtUtc,String pendingCauseSha256,
            String writerHeadSha256,long writerHeadSequence,String newEpisodeRunId,int successorCharacterId,
            FinalClearance modal,int dateRaw,ExactRef actualOrdinarySnapshot,ExactRef actualObservation,ExactRef currentRoot,ExactRef currentRootRead,
            ExactRef originalKnown,ExactRef originalSemantic,ExactRef pendingContinueReceipt,ExactRef pendingContinueDriver,
            ExactRef canonicalPublication,Optional<ExactRef> sourceQualification,ExactRef initialTimeline,List<ExactRef> postqueries,
            Optional<ExactRef> close,Optional<ExactRef> verifiedDateAdvance,Optional<ExactRef> finalTimelineAfterDateAdvance) {
        public FinalProofDocument {
            StrictJson.text(machineId);Objects.requireNonNull(observedAtUtc);StrictJson.utc(observedAtUtc.toString());
            finalDigest(pendingCauseSha256);finalDigest(writerHeadSha256);StrictJson.safe(writerHeadSequence,0);
            StrictJson.text(newEpisodeRunId);StrictJson.require(successorCharacterId>0,"private final successor must be positive");Objects.requireNonNull(modal);
            postqueries=List.copyOf(postqueries);Objects.requireNonNull(close);Objects.requireNonNull(verifiedDateAdvance);Objects.requireNonNull(finalTimelineAfterDateAdvance);
            for(ExactRef ref:List.of(actualOrdinarySnapshot,actualObservation,currentRoot,currentRootRead,originalKnown,originalSemantic,
                    pendingContinueReceipt,pendingContinueDriver,canonicalPublication,initialTimeline))finalRef(ref);
            Objects.requireNonNull(sourceQualification);sourceQualification.ifPresent(RootPendingNaturalSuccessionQualification::finalRef);
            postqueries.forEach(RootPendingNaturalSuccessionQualification::finalRef);close.ifPresent(RootPendingNaturalSuccessionQualification::finalRef);
            verifiedDateAdvance.ifPresent(RootPendingNaturalSuccessionQualification::finalRef);finalTimelineAfterDateAdvance.ifPresent(RootPendingNaturalSuccessionQualification::finalRef);
            StrictJson.require(close.isPresent()==verifiedDateAdvance.isPresent()&&close.isPresent()==finalTimelineAfterDateAdvance.isPresent(),"final Close/date/query material presence differs");
            StrictJson.require(close.isPresent()?!postqueries.isEmpty()&&postqueries.size()<=8:postqueries.isEmpty(),"bounded actual post-Close originals required");
            StrictJson.require(postqueries.stream().distinct().count()==postqueries.size(),"duplicate final postquery original");
            StrictJson.require((modal==FinalClearance.CLOSED_AND_DATE_ADVANCED)==close.isPresent(),"final modal result and original Close materials differ");
        }
        /** The actual Domain Import producer consumes this exact finite typed closure. */
        public List<ExactRef> materialReferences() {
            var refs=new ArrayList<>(List.of(actualOrdinarySnapshot,actualObservation,currentRoot,currentRootRead,originalKnown,originalSemantic,
                    pendingContinueReceipt,pendingContinueDriver,canonicalPublication,initialTimeline));
            sourceQualification.ifPresent(refs::add);
            refs.addAll(postqueries);close.ifPresent(refs::add);verifiedDateAdvance.ifPresent(refs::add);finalTimelineAfterDateAdvance.ifPresent(refs::add);
            return refs.stream().distinct().toList();
        }
    }
    public static byte[] encodeFinalProof(FinalProofDocument value) {
        Objects.requireNonNull(value);var out=StrictJson.object().put("schema",FINAL_PROOF_SCHEMA).put("machine_id",value.machineId())
                .put("observed_at_utc",value.observedAtUtc().toString()).put("pending_cause_sha256",value.pendingCauseSha256())
                .put("writer_head_sha256",value.writerHeadSha256()).put("writer_head_sequence",value.writerHeadSequence())
                .put("new_episode_run_id",value.newEpisodeRunId()).put("successor_character_id",value.successorCharacterId())
                .put("modal",value.modal().wire()).put("date_raw",value.dateRaw()).put("replay_authorized",false).put("business_reapply_authorized",false);
        out.set("actual_ordinary_snapshot",value.actualOrdinarySnapshot().toJson());out.set("actual_observation",value.actualObservation().toJson());out.set("current_root",value.currentRoot().toJson());out.set("current_root_read",value.currentRootRead().toJson());
        out.set("original_known",value.originalKnown().toJson());out.set("original_semantic",value.originalSemantic().toJson());
        out.set("pending_continue_receipt",value.pendingContinueReceipt().toJson());out.set("pending_continue_driver",value.pendingContinueDriver().toJson());
        out.set("canonical_publication",value.canonicalPublication().toJson());finalOptional(out,"source_qualification",value.sourceQualification());out.set("initial_timeline",value.initialTimeline().toJson());
        var post=out.putArray("postqueries");value.postqueries().forEach(ref->post.add(ref.toJson()));
        finalOptional(out,"close",value.close());finalOptional(out,"verified_date_advance",value.verifiedDateAdvance());finalOptional(out,"final_timeline_after_date_advance",value.finalTimelineAfterDateAdvance());
        return StrictJson.canonical(out,FINAL_PROOF_MAX_BYTES);
    }
    public static FinalProofDocument decodeFinalProof(byte[] original) {
        var row=StrictJson.object(StrictJson.parse(original,FINAL_PROOF_MAX_BYTES),FINAL_PROOF_FIELDS,Set.of("source_qualification"));
        StrictJson.require(FINAL_PROOF_SCHEMA.equals(StrictJson.text(row.get("schema"))),"final v2 complete materials required; v1 lacks a bound ROOT read");
        for(String field:List.of("replay_authorized","business_reapply_authorized")){var flag=row.get(field);StrictJson.require(flag.isBoolean()&&!flag.booleanValue(),"final DATA cannot authorize replay or reapply");}
        var post=row.get("postqueries");StrictJson.require(post.isArray()&&post.size()<=8,"bounded final postqueries array required");var refs=new ArrayList<ExactRef>();post.forEach(value->refs.add(ExactRef.fromJson(value)));
        return new FinalProofDocument(StrictJson.text(row.get("machine_id")),Instant.parse(StrictJson.utc(StrictJson.text(row.get("observed_at_utc")))),
                StrictJson.text(row.get("pending_cause_sha256")),StrictJson.text(row.get("writer_head_sha256")),StrictJson.integer(row.get("writer_head_sequence"),0,StrictJson.MAX_SAFE_INTEGER),
                StrictJson.text(row.get("new_episode_run_id")),(int)StrictJson.integer(row.get("successor_character_id"),1,Integer.MAX_VALUE),FinalClearance.parse(StrictJson.text(row.get("modal"))),
                (int)StrictJson.integer(row.get("date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE),ExactRef.fromJson(row.get("actual_ordinary_snapshot")),ExactRef.fromJson(row.get("actual_observation")),ExactRef.fromJson(row.get("current_root")),
                ExactRef.fromJson(row.get("current_root_read")),ExactRef.fromJson(row.get("original_known")),ExactRef.fromJson(row.get("original_semantic")),ExactRef.fromJson(row.get("pending_continue_receipt")),
                ExactRef.fromJson(row.get("pending_continue_driver")),ExactRef.fromJson(row.get("canonical_publication")),ExactRef.optionalFromJson(row.get("source_qualification")),ExactRef.fromJson(row.get("initial_timeline")),
                refs,finalOptional(row.get("close")),finalOptional(row.get("verified_date_advance")),finalOptional(row.get("final_timeline_after_date_advance")));
    }
    private static void finalDigest(String value){StrictJson.require(value!=null&&value.matches("[0-9a-f]{64}"),"final original SHA256 required");}
    private static void finalRef(ExactRef ref){StrictJson.require(Objects.requireNonNull(ref).bytes()>0&&ref.bytes()<=RawJson.MAXIMUM_BYTES,"bounded complete final material reference required");}
    private static Optional<ExactRef> finalOptional(JsonNode value){StrictJson.require(value!=null,"missing explicit final optional field");return value.isNull()?Optional.empty():Optional.of(ExactRef.fromJson(value));}
    private static void finalOptional(ObjectNode row,String field,Optional<ExactRef> value){if(value.isPresent())row.set(field,value.orElseThrow().toJson());else row.putNull(field);}
    public static final class PendingCause {
        private final RootPendingNaturalSuccessionQualification owner;
        private final ActionCommand parent;private final LifecycleObservationPort.Snapshot before;
        private final Head head;private final CauseOriginals originals;private final int predecessor,successor;
        private final byte[] proof;private final String digest;
        private PendingCause(RootPendingNaturalSuccessionQualification owner,ActionCommand parent,
                LifecycleObservationPort.Snapshot before,Head head,CauseOriginals originals,int predecessor,
                int successor,byte[] proof){this.owner=owner;this.parent=parent;this.before=before;this.head=head;
            this.originals=originals;this.predecessor=predecessor;this.successor=successor;this.proof=proof.clone();
            digest=G2RetainedNativeSourceProvider.sha256(proof);}
        public String causeDigest(){return digest;} public byte[] originalProof(){return proof.clone();}
        public String parentBodySha256(){return ActionCodec.bodySha256(parent);}
        public int predecessorCharacterId(){return predecessor;}public int successorCharacterId(){return successor;}
        public String oldEpisodeRunId(){return originals.originals().session().episodeRunId();}
        public long episodeEpoch(){return before.facts().stamp().episodeEpoch();}
        public long driverVersion(){return before.facts().stamp().driverVersion();}
        public Head precommitHead(){return head;}
        public ExactRef predecessorRoot(){return originals.originals().predecessorRoot();}
        public ExactRef engineClockProof(){return originals.originals().engineClockAndActorProof();}
        public ExactRef precommitSnapshot(){return before.originalEvidence();}
        public LifecycleIdentity predecessorDeathOrigin(){return originals.originals().predecessorDeath().request().origin().requireLifecycleTerminal();}
    }
    public static final class Finalized {
        private final PendingCause cause;private final String modal,digest;private final ExactRef currentSnapshot;
        private final FinalOriginals originals;private final byte[] proof;private final Optional<ExactRef> continuityBinding;
        private Finalized(PendingCause cause,String modal,ExactRef currentSnapshot,FinalOriginals originals,byte[] proof){
            this(cause,modal,currentSnapshot,originals,proof,Optional.empty());}
        private Finalized(PendingCause cause,String modal,ExactRef currentSnapshot,FinalOriginals originals,byte[] proof,Optional<ExactRef> continuityBinding){
            this.cause=cause;this.modal=modal;this.currentSnapshot=currentSnapshot;this.originals=originals;this.proof=proof.clone();digest=G2RetainedNativeSourceProvider.sha256(proof);this.continuityBinding=Objects.requireNonNull(continuityBinding);}
        public String digest(){return digest;}public String causeDigest(){return cause.causeDigest();}
        public String modal(){return modal;}public ExactRef currentSnapshot(){return currentSnapshot;}
        public FinalOriginals originals(){return originals;}public byte[] originalProof(){return proof.clone();}
        public Optional<ExactRef> continuityBinding(){return continuityBinding;}
    }
    private final RootCausePort causePort;private final RootFinalPort finalPort;
    private final Optional<RootRetainedCausePort> retainedPort;
    private final Optional<RootRetainedFinalizationPort> retainedFinalPort;
    private final Optional<RootRetainedContinuityPort> continuityPort;
    public RootPendingNaturalSuccessionQualification(RootCausePort causePort,RootFinalPort finalPort){this.causePort=Objects.requireNonNull(causePort);this.finalPort=Objects.requireNonNull(finalPort);this.retainedPort=Optional.empty();this.retainedFinalPort=Optional.empty();this.continuityPort=Optional.empty();}
    public RootPendingNaturalSuccessionQualification(RootCausePort causePort,RootFinalPort finalPort,RootRetainedCausePort retainedPort){this.causePort=Objects.requireNonNull(causePort);this.finalPort=Objects.requireNonNull(finalPort);this.retainedPort=Optional.of(Objects.requireNonNull(retainedPort));this.retainedFinalPort=Optional.empty();this.continuityPort=Optional.empty();}
    public RootPendingNaturalSuccessionQualification(RootCausePort causePort,RootFinalPort finalPort,RootRetainedCausePort retainedPort,RootRetainedFinalizationPort retainedFinalPort){this.causePort=Objects.requireNonNull(causePort);this.finalPort=Objects.requireNonNull(finalPort);this.retainedPort=Optional.of(Objects.requireNonNull(retainedPort));this.retainedFinalPort=Optional.of(Objects.requireNonNull(retainedFinalPort));this.continuityPort=Optional.empty();}
    public RootPendingNaturalSuccessionQualification(RootCausePort causePort,RootFinalPort finalPort,RootRetainedCausePort retainedPort,RootRetainedFinalizationPort retainedFinalPort,RootRetainedContinuityPort continuityPort){this.causePort=Objects.requireNonNull(causePort);this.finalPort=Objects.requireNonNull(finalPort);this.retainedPort=Optional.of(Objects.requireNonNull(retainedPort));this.retainedFinalPort=Optional.of(Objects.requireNonNull(retainedFinalPort));this.continuityPort=Optional.of(Objects.requireNonNull(continuityPort));}
    public PendingCause qualify(ActionCommand parent,LifecycleObservationPort.Snapshot actual,Head head)throws IOException {
        return qualifyUsing(causePort,parent,actual,head);
    }
    private PendingCause qualifyUsing(RootCausePort qualifiedPort,ActionCommand parent,LifecycleObservationPort.Snapshot actual,Head head)throws IOException {
        Objects.requireNonNull(parent);Objects.requireNonNull(actual);Objects.requireNonNull(head);
        try{
            StrictJson.require(parent.operation().value().equals("continue-as-reconciled-successor"),"original natural Continue parent required");
            CauseOriginals original=Objects.requireNonNull(qualifiedPort.openQualified(parent,actual,head));Originals held=original.originals();
            var transport=actual.actual().session();Session session=held.session();
            StrictJson.require(session.machineId().equals(transport.machineId())&&session.sessionId().equals(transport.sessionId())
                    &&session.game().pid()==transport.game().pid()&&session.game().creationFiletime().equals(transport.game().creationFiletime().value().toString())
                    &&session.connectionGeneration().equals(transport.connectionGeneration().toString())
                    &&session.episodeRunId().equals(actual.facts().driver().session().episodeRunId())
                    &&session.executable().sha256().equals(org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.EXE_SHA256)
                    &&parent.source().equals(actual.source()),"actual precommit physical Game/source/episode differs");
            JsonNode semantic=OpportunityJson.toNode(actual.semantic()),player=required(semantic,"played_character");StrictJson.trueValue(required(player,"alive"));
            int successor=(int)StrictJson.integer(required(player,"character_id"),1,Integer.MAX_VALUE);
            int predecessor=actual.facts().driver().session().actorId().intValueExact();
            StrictJson.require(predecessor>0&&predecessor!=successor&&"played_character_changed".equals(StrictJson.text(required(semantic,"one_life_terminal_reason")))&&actual.paused()&&actual.mapReady(),"paused living actual successor and old terminal subject required");
            Frame before=held.predecessorFrame();StrictJson.require(before.actorCharacterId()==predecessor&&actual.dateRaw().compareTo(BigInteger.valueOf(before.dateRaw()))>=0,"original predecessor/date differs");
            byte[] root=exact(qualifiedPort,held.predecessorRoot());RootOriginalNaturalSuccessionVerifier.requireOriginalPlayerHeir(root,before,successor);
            var receipt=held.predecessorDeath();var request=receipt.request();var terminal=request.origin().requireLifecycleTerminal();var frame=terminal.frame();
            StrictJson.require(request.source().equals(actual.source())&&request.sessionId().equals(parent.sessionId())
                    &&receipt.before().binding().connectionGeneration().equals(transport.connectionGeneration())&&receipt.after().binding().connectionGeneration().equals(transport.connectionGeneration())
                    &&terminal.machineId().equals(transport.machineId())&&terminal.game().equals(transport.game())
                    &&terminal.subject().episodeRunId().equals(session.episodeRunId())&&terminal.subject().characterId().intValueExact()==predecessor
                    &&terminal.subject().episodeEpoch()==actual.facts().stamp().episodeEpoch()&&terminal.subject().driverVersion()==actual.facts().stamp().driverVersion()
                    &&frame.revision().compareTo(actual.revision())<=0&&frame.nativeRevision().compareTo(actual.actual().nativeRevision())<=0
                    &&frame.dateRaw().equals(actual.dateRaw())&&frame.paused()&&frame.mapReady()
                    &&terminal.currentPlayer() instanceof LifecycleIdentity.Character controlled&&controlled.alive()&&controlled.characterId().intValueExact()==successor,
                    "independent retained predecessor death crossed actual terminal subject/frame");
            var arguments=PrisonerOptionIntent.decode(OpportunityJson.encode(request.arguments()));
            StrictJson.require(arguments.materialTarget().isPresent()&&arguments.materialTarget().getAsLong()==Integer.toUnsignedLong(predecessor),"retained death query did not independently name predecessor");
            var custody=PrisonerTerminalQueries.decode(receipt).retainedCustody();StrictJson.require(custody.isPresent()&&custody.orElseThrow() instanceof PrisonerMaterial12004.Dead,"independent actual predecessor Dead required");
            NaturalEngineClockProof.decode(exact(qualifiedPort,held.engineClockAndActorProof())).requireBoundTo(transport.machineId(),actual.actual().observedAt(),head.digest(),held.predecessorRoot(),actual.originalEvidence());
            var estate=original.estate();var comparison=estate.comparison();
            StrictJson.require(java.util.Arrays.equals(root,estate.predecessor().originalRootResult())
                    &&comparison.verdict()==Verdict.MATCHED&&comparison.successorMatch()&&comparison.titleDistributionMatch()
                    &&comparison.predecessorCharacterId()==predecessor&&comparison.actualSuccessorCharacterId()==successor
                    &&comparison.predecessorBinding().episodeRunId().equals(session.episodeRunId())
                    &&comparison.successorBinding().revision().equals(actual.revision())&&comparison.successorBinding().nativeRevision().equals(actual.actual().nativeRevision())
                    &&comparison.successorBinding().dateRaw()==actual.dateRaw().intValueExact()
                    &&FullJsonTree.parse(estate.originalSemantic(),FullJsonTree.MAXIMUM_BYTES).equals(FullJsonTree.parse(DriverJson.encode(actual.semantic()),FullJsonTree.MAXIMUM_BYTES)),
                    "actual complete estate reconciliation crossed old episode/current original frame");
            StrictJson.require(java.util.Arrays.equals(root,exact(qualifiedPort,held.predecessorRoot())),"preclock getter original drift");
            requireEstateOriginals(qualifiedPort,original,actual);
            qualifiedPort.requireCurrent(original,parent,actual,head);
            var material=original.estateOriginals();
            var proof=new PendingNaturalCauseProof.Document(transport.machineId(),actual.actual().observedAt(),ActionCodec.bodySha256(parent),
                    head.digest(),head.state().sequence(),predecessor,successor,session.episodeRunId(),actual.facts().stamp().episodeEpoch(),
                    actual.facts().stamp().driverVersion(),held.predecessorRoot(),held.engineClockAndActorProof(),actual.originalEvidence(),
                    material.readReference(),material.resultReference(),material.semanticReference(),material.originalKnown(),
                    G2RetainedNativeSourceProvider.sha256(estate.wire()),G2RetainedNativeSourceProvider.sha256(receipt.original().originalPacket()));
            return new PendingCause(this,parent,actual,head,original,predecessor,successor,PendingNaturalCauseProof.encode(proof));
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("pending natural cause remains unqualified: "+invalid.getMessage(),invalid);}
    }
    /** Replays retained v2 originals inside the actual installed historical Root port. No JSON decoder
     * or new observation can substitute for the old terminal snapshot, exact Head or missing materials. */
    public PendingCause qualifyRetainedCause(ExactRef retainedProof,FullSnapshot current,ContinuityStorePort.Session same,
            SourceQualification source,Head currentHead)throws IOException {
        Objects.requireNonNull(retainedProof);Objects.requireNonNull(current);Objects.requireNonNull(same);Objects.requireNonNull(source);Objects.requireNonNull(currentHead);
        RootRetainedCausePort authority=retainedPort.orElseThrow(()->new IOException("actual retained-cause Root authority is not installed"));
        try {
            source.assertCurrent(same);
            StrictJson.require(same.head().digest().equals(currentHead.digest()),"retained cause caller lost the actual current writer head");
            RetainedOriginals historical=Objects.requireNonNull(authority.openRetainedQualified(retainedProof,current,same,source,currentHead));
            byte[] raw=exactMaterial(historical.historicalPort(),retainedProof,PendingNaturalCauseProof.MAX_BYTES);
            var document=PendingNaturalCauseProof.decode(raw);
            StrictJson.require(document.writerHeadSequence()==historical.precommitHead().state().sequence()
                    &&document.writerHeadSha256().equals(historical.precommitHead().digest())
                    &&historical.precommitHead().state().sequence()<=currentHead.state().sequence(),"retained cause needs its exact real historical head/sequence");
            PendingCause rederived=qualifyUsing(historical.historicalPort(),historical.parent(),historical.oldTerminal(),historical.precommitHead());
            StrictJson.require(java.util.Arrays.equals(raw,rederived.originalProof())&&retainedProof.sha256().equals(rederived.causeDigest()),
                    "retained original cause did not rederive identical bytes/digest from the original complete materials");
            var old=rederived.before.actual().session();var transport=current.actual().session();var driver=current.facts().driver().session();
            StrictJson.require(transport.machineId().equals(old.machineId())&&transport.game().equals(old.game())
                    &&transport.sessionId().equals(old.sessionId())&&transport.connectionGeneration().equals(old.connectionGeneration())
                    &&current.facts().source().equals(rederived.before.source())&&current.facts().transport().equals(transport)
                    &&driver.actorId().intValueExact()==rederived.successor&&!driver.episodeRunId().equals(rederived.oldEpisodeRunId())
                    &&current.facts().episodeEpoch()==Math.addExact(rederived.episodeEpoch(),1)&&current.facts().driverVersion()>rederived.driverVersion(),
                    "retained cause may rebind only the actual same physical/source/session/connection successor episode");
            FullSnapshot replayed=new DriverObservationAssembler().projectFull(current.actual(),current.facts(),current.originalEvidence());
            StrictJson.require(replayed.semantic().equals(current.semantic())&&replayed.fullBindingSha256().equals(current.fullBindingSha256()),
                    "actual current cold frame differs from the sole complete native/Driver projection");
            JsonNode semantic=OpportunityJson.toNode(current.semantic()),player=required(semantic,"played_character");
            StrictJson.trueValue(required(player,"alive"));
            StrictJson.require(StrictJson.integer(required(player,"character_id"),1,Integer.MAX_VALUE)==rederived.successor
                    &&required(semantic,"one_life_terminal_reason").isNull()
                    &&StrictJson.integer(required(semantic,"date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE)>=rederived.before.dateRaw().intValueExact(),
                    "retained cause cannot substitute a terminal actor or regressed current source date");
            source.assertCurrent(same);
            authority.requireRetainedCurrent(historical,retainedProof,rederived,current,same,source,currentHead);
            StrictJson.require(same.head().digest().equals(currentHead.digest()),"retained cause history/source revalidation changed the current writer head");
            return rederived;
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("retained natural cause remains missing or unqualified: "+invalid.getMessage(),invalid);}
    }
    /** Explicit fresh-transport path. The historical cause proof remains byte-identical. */
    public ReconnectedCause qualifyRetainedCauseReconnected(ExactRef retainedProof,FullSnapshot current,
            ContinuityStorePort.Session same,SourceQualification source,Head head)throws IOException {
        Objects.requireNonNull(retainedProof);Objects.requireNonNull(current);Objects.requireNonNull(same);Objects.requireNonNull(source);Objects.requireNonNull(head);
        var historicalPort=retainedPort.orElseThrow(()->new IOException("actual retained-cause Root authority is not installed"));
        var continuity=continuityAuthority();
        try {
            source.assertCurrent(same);requireHead(same,head);
            var historical=Objects.requireNonNull(historicalPort.openRetainedQualified(retainedProof,current,same,source,head));
            byte[] raw=exactMaterial(historical.historicalPort(),retainedProof,PendingNaturalCauseProof.MAX_BYTES);
            var document=PendingNaturalCauseProof.decode(raw);
            StrictJson.require(document.writerHeadSequence()==historical.precommitHead().state().sequence()
                    &&document.writerHeadSha256().equals(historical.precommitHead().digest())
                    &&historical.precommitHead().state().sequence()<=head.state().sequence(),"reconnect requires the exact historical cause head");
            PendingCause cause=qualifyUsing(historical.historicalPort(),historical.parent(),historical.oldTerminal(),historical.precommitHead());
            StrictJson.require(java.util.Arrays.equals(raw,cause.originalProof())&&retainedProof.sha256().equals(cause.causeDigest()),
                    "reconnect cannot alter or replace the historical cause originals");
            requireSameGameSuccessor(cause,current,true);
            var originals=Objects.requireNonNull(continuity.openQualified(cause,retainedProof,current,same,source,head));
            var custody=new ReconnectedCause(this,cause,historical,retainedProof,originals,current,same,source,head);
            requireReconnectedCauseCurrent(custody,current,same,source,head);
            return custody;
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("same-Game retained cause remains unqualified: "+invalid.getMessage(),invalid);}
    }
    public void requireReconnectedCauseCurrent(ReconnectedCause custody,FullSnapshot current,
            ContinuityStorePort.Session same,SourceQualification source,Head head)throws IOException {
        Objects.requireNonNull(custody);Objects.requireNonNull(current);Objects.requireNonNull(same);Objects.requireNonNull(source);Objects.requireNonNull(head);
        var authority=continuityAuthority();var historicalPort=retainedPort.orElseThrow(()->new IOException("actual retained-cause Root authority is not installed"));
        StrictJson.require(custody.owner==this&&custody.cause.owner==this&&custody.current==current&&custody.same==same&&custody.source==source
                &&custody.head.digest().equals(head.digest())&&custody.head.state().sequence()==head.state().sequence(),
                "reconnect custody escaped its original physical/writer/source scope; a fresh frame requires new qualification");
        source.assertCurrent(same);requireHead(same,head);
        requireSameGameSuccessor(custody.cause,current,true);
        requireContinuityBinding(authority,custody.continuity,custody.cause,custody.retainedProof,current,source.proof(),same,head,ContinuityPhase.PREPARED_CURRENT);
        StrictJson.require(java.util.Arrays.equals(exactMaterial(custody.historical.historicalPort(),custody.retainedProof,
                PendingNaturalCauseProof.MAX_BYTES),custody.cause.originalProof()),"original retained cause changed before reconnect use");
        historicalPort.requireRetainedCurrent(custody.historical,custody.retainedProof,custody.cause,current,same,source,head);
        authority.requireCurrent(custody.continuity,custody.cause,custody.retainedProof,current,same,source,head);
        source.assertCurrent(same);requireHead(same,head);
    }
    private RootRetainedContinuityPort continuityAuthority()throws IOException {
        return continuityPort.orElseThrow(()->new IOException("actual same-Game physical continuity Root authority is not installed"));
    }
    private static void requireHead(ContinuityStorePort.Session same,Head head)throws IOException {
        StrictJson.require(same.head().digest().equals(head.digest())&&same.head().state().sequence()==head.state().sequence(),
                "same-Game continuity lost the exact current writer head");
    }
    private static boolean sameTransport(FullSnapshot current,PendingCause cause) {
        var old=cause.before.actual().session();var now=current.actual().session();
        return old.sessionId().equals(now.sessionId())&&old.connectionGeneration().equals(now.connectionGeneration());
    }
    private static void requireSameGameSuccessor(PendingCause cause,FullSnapshot current,boolean freshTransport) {
        var old=cause.before.actual().session();var now=current.actual().session();var driver=current.facts().driver().session();
        StrictJson.require(now.machineId().equals(old.machineId())&&now.game().equals(old.game())
                &&(!freshTransport||!sameTransport(current,cause))&&current.facts().transport().equals(now)
                &&current.facts().source().equals(cause.before.source())&&driver.actorId().intValueExact()==cause.successor
                &&!driver.episodeRunId().equals(cause.oldEpisodeRunId())&&current.facts().episodeEpoch()==Math.addExact(cause.episodeEpoch(),1)
                &&current.facts().driverVersion()>cause.driverVersion()
                &&!current.actual().observedAt().isBefore(cause.before.actual().observedAt()),
                "same OS Game/source, fresh actual transport, canonical successor and monotone native/Driver observation required");
        PendingSameGameContinuity.requireRevisionContinuation(new PendingSameGameContinuity.RevisionFrame(old.sessionId(),
                old.connectionGeneration().toString(),cause.before.revision(),cause.before.actual().nativeRevision(),cause.before.dateRaw().intValueExact()),revisionFrame(current));
        var projected=new DriverObservationAssembler().projectFull(current.actual(),current.facts(),current.originalEvidence());
        StrictJson.require(projected.semantic().equals(current.semantic())&&projected.fullBindingSha256().equals(current.fullBindingSha256()),
                "current reconnect frame differs from the complete native/Driver projection");
        var semantic=OpportunityJson.toNode(current.semantic());var player=required(semantic,"played_character");StrictJson.trueValue(required(player,"alive"));
        StrictJson.require(StrictJson.integer(required(player,"character_id"),1,Integer.MAX_VALUE)==cause.successor
                &&required(semantic,"one_life_terminal_reason").isNull()
                &&StrictJson.integer(required(semantic,"date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE)>=cause.before.dateRaw().intValueExact(),
                "reconnect current successor/terminal/date differs from the original natural cause");
    }
    private static void requireCanonicalPin(ContinuityStorePort.Session same,ExactRef reference)throws IOException {
        var pin=same.head().documents().stream().filter(value->value.reference().equals(reference)).findFirst()
                .orElseThrow(()->new IOException("same-Game continuity original is absent from canonical writer pins: "+reference.path()));
        same.verifyPin(pin);
    }
    private static PendingSameGameContinuity.RevisionFrame revisionFrame(FullSnapshot frame) {
        var transport=frame.actual().session();int date=(int)StrictJson.integer(required(OpportunityJson.toNode(frame.semantic()),"date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE);
        return new PendingSameGameContinuity.RevisionFrame(transport.sessionId(),transport.connectionGeneration().toString(),
                frame.facts().publicRevision(),frame.actual().nativeRevision(),date);
    }
    private enum ContinuityPhase { PREPARED_CURRENT,CANONICAL_HISTORICAL }
    private static void requireContinuityBinding(RootRetainedContinuityPort port,ContinuityOriginals originals,PendingCause cause,
            ExactRef retainedProof,FullSnapshot frame,Optional<ExactRef> sourceProof,ContinuityStorePort.Session same,Head head,ContinuityPhase phase)throws IOException {
        byte[] raw=exactMaterial(port,originals.binding(),PendingSameGameContinuity.MAX_BYTES);
        var binding=PendingSameGameContinuity.decode(raw);
        StrictJson.require(binding.equals(originals.document())&&java.util.Arrays.equals(raw,PendingSameGameContinuity.encode(binding)),
                "same-Game binding is not the exact sole producer/codec document");
        var old=cause.before.actual().session();var now=frame.actual().session();var driver=frame.facts().driver().session();
        StrictJson.require(binding.machineId().equals(old.machineId())&&binding.machineId().equals(now.machineId())&&now.game().equals(old.game())
                &&binding.gamePid()==now.game().pid()&&binding.gameCreationFiletimeDecimal().equals(now.game().creationFiletime().value().toString())
                &&binding.gameExecutable().equals(cause.originals.originals().session().executable())
                &&binding.retainedCauseProof().equals(retainedProof)&&retainedProof.sha256().equals(cause.causeDigest())
                &&binding.originalSessionId().equals(old.sessionId())&&binding.originalConnectionGenerationDecimal().equals(old.connectionGeneration().toString())
                &&binding.currentSessionId().equals(now.sessionId())&&binding.currentConnectionGenerationDecimal().equals(now.connectionGeneration().toString())
                &&binding.historicalNative().equals(cause.before.originalEvidence())&&binding.currentNative().equals(frame.originalEvidence())
                &&binding.currentObservation().equals(frame.facts().semanticFactsEvidence())&&binding.currentSourceQualification().equals(sourceProof)
                &&binding.successorCharacterId()==cause.successor&&driver.actorId().intValueExact()==cause.successor
                &&binding.successorEpisodeRunId().equals(driver.episodeRunId())&&binding.episodeEpoch()==frame.facts().episodeEpoch()
                &&binding.driverVersion()==frame.facts().driverVersion()&&binding.observedAtUtc().equals(frame.actual().observedAt())
                &&binding.writerHeadSequence()>=cause.head.state().sequence()&&binding.writerHeadSequence()<=head.state().sequence(),
                "canonical continuity DATA crossed its exact old/current Game, transport, source, frame, successor or writer");
        same.requireHistoricalHead(binding.writerHeadSequence(),binding.writerHeadSha256());
        for(ExactRef reference:List.of(retainedProof,binding.historicalNative()))requireCanonicalPin(same,reference);

        if(phase==ContinuityPhase.CANONICAL_HISTORICAL) {
            requireCanonicalPin(same,originals.binding());
            for(ExactRef reference:binding.materialReferences())requireCanonicalPin(same,reference);
        }
        var known=DriverSnapshotFacts.decodeKnownOriginal(DriverSnapshotFacts.originalKnownJson(
                exactMaterial(port,binding.currentKnown(),DriverSnapshotFacts.MAX_ORIGINAL_BYTES)),Optional.of(frame.facts()));
        StrictJson.require(java.util.Arrays.equals(DriverSnapshotFacts.encodeKnownOriginal(known).bytes(),
                DriverSnapshotFacts.encodeKnownOriginal(originals.actualKnown()).bytes()),"same-Game continuity requires all seven exact current Known slots");
        exactMaterial(port,binding.currentNative(),RawJson.MAXIMUM_BYTES);exactMaterial(port,binding.currentObservation(),RawJson.MAXIMUM_BYTES);

    }
    private static void requireEstateOriginals(RootCausePort port,CauseOriginals original,LifecycleObservationPort.Snapshot actual)throws IOException {
        EstateOriginals retained=original.estateOriginals();var read=retained.successorRootRead();
        var origin=read.request().origin().requireLifecycleTerminal();var transport=actual.actual().session();var frame=origin.frame();
        StrictJson.require(read.request().source().equals(actual.source())&&read.request().sessionId().equals(transport.sessionId())
                &&origin.machineId().equals(transport.machineId())&&origin.game().equals(transport.game())
                &&origin.connectionGeneration().equals(transport.connectionGeneration())
                &&origin.subject().characterId().equals(actual.facts().driver().session().actorId())
                &&origin.subject().episodeRunId().equals(actual.facts().driver().session().episodeRunId())
                &&origin.subject().episodeEpoch()==actual.facts().stamp().episodeEpoch()&&origin.subject().driverVersion()==actual.facts().stamp().driverVersion()
                &&frame.snapshotId().equals(actual.actual().snapshotId())&&frame.revision().equals(actual.revision())
                &&frame.nativeRevision().equals(actual.actual().nativeRevision())&&frame.dateRaw().equals(actual.dateRaw())
                &&frame.paused()&&frame.mapReady()&&origin.nativeEvidence().equals(actual.originalEvidence()),
                "first successor ROOT receipt differs from the actual retained old-subject terminal frame");
        byte[] result=exact(port,retained.resultReference());
        StrictJson.require(read.original().originalResultToken().isPresent()
                &&java.util.Arrays.equals(read.original().originalResultToken().orElseThrow().bytes(),result)
                &&java.util.Arrays.equals(result,original.estate().originalRootResult()),"successor estate result token differs from the complete first native ROOT original");
        exactMaterial(port,retained.readReference(),RawJson.MAXIMUM_BYTES);
        byte[] semantic=exactMaterial(port,retained.semanticReference(),FullJsonTree.MAXIMUM_BYTES);
        StrictJson.require(java.util.Arrays.equals(semantic,original.estate().originalSemantic())
                &&FullJsonTree.parse(semantic,FullJsonTree.MAXIMUM_BYTES).equals(FullJsonTree.parse(DriverJson.encode(actual.semantic()),FullJsonTree.MAXIMUM_BYTES)),
                "successor estate semantic original differs from the complete retained actual frame");
        var known=DriverSnapshotFacts.decodeKnownOriginal(DriverSnapshotFacts.originalKnownJson(exactMaterial(port,retained.originalKnown(),DriverSnapshotFacts.MAX_ORIGINAL_BYTES)),actual.facts().observation());
        StrictJson.require(java.util.Arrays.equals(DriverSnapshotFacts.encodeKnownOriginal(known).bytes(),DriverSnapshotFacts.encodeKnownOriginal(actual.facts()).bytes()),
                "retained Known must include the exact original complete Driver/history/actions/auxiliary/loop/observation facts");
    }
    /** Requalifies an already-committed final business transition. It cannot authorize that CAS again. */
    public RetainedFinalized qualifyRetainedFinalization(PendingCause cause,ExactRef retainedProof,FullSnapshot current,
            ContinuityStorePort.Session same,SourceQualification actualCurrentSource,Head actualCurrentHead)throws IOException {
        Objects.requireNonNull(cause);Objects.requireNonNull(retainedProof);Objects.requireNonNull(current);Objects.requireNonNull(same);
        Objects.requireNonNull(actualCurrentSource);Objects.requireNonNull(actualCurrentHead);
        RootRetainedFinalizationPort authority=retainedFinalPort.orElseThrow(()->new IOException("actual retained-finalization Root authority is not installed"));
        try {
            StrictJson.require(cause.owner==this,"retained finalization requires this private original cause issuer");
            actualCurrentSource.assertCurrent(same);
            StrictJson.require(same.head().digest().equals(actualCurrentHead.digest()),"retained final caller lost the actual current writer head");
            var original=Objects.requireNonNull(authority.openRetainedQualified(cause,retainedProof,current,same,actualCurrentSource,actualCurrentHead));
            byte[] raw=exactMaterial(original.evidence(),retainedProof,FINAL_PROOF_MAX_BYTES);var document=decodeFinalProof(raw);
            var recordedHead=same.requireHistoricalHead(document.writerHeadSequence(),document.writerHeadSha256());
            StrictJson.require(recordedHead.digest().equals(original.beforeFinalHead().digest())
                    &&recordedHead.state().sequence()==original.beforeFinalHead().state().sequence()
                    &&recordedHead.state().sequence()<=actualCurrentHead.state().sequence()
                    &&document.pendingCauseSha256().equals(cause.causeDigest())
                    &&(document.sourceQualification().isPresent()==original.originalSourceQualification().isPresent()
                        &&document.sourceQualification().equals(original.originalSourceQualification())),
                    "retained finalization lacks its exact genuine predecessor Head/cause/original source proof");
            Finalized replayed=finalizeUsing(cause,original.beforeFinal(),same,original.beforeFinalHead(),
                    original.originalSourceQualification(),original.originals(),original.evidence(),original.evidence()::openQualifiedModalQuery,
                    ()->{actualCurrentSource.assertCurrent(same);authority.requireRetainedCurrent(original,cause,retainedProof,current,same,actualCurrentSource,actualCurrentHead);});
            StrictJson.require(java.util.Arrays.equals(raw,replayed.originalProof())&&retainedProof.sha256().equals(replayed.digest()),
                    "historical finalization did not rederive the identical complete v2 proof");
            requireRetainedCanonicalLifecycle(cause,original,retainedProof,document,same);
            requireRetainedFinalFrame(cause,original.beforeFinal(),current,original.canonicalLifecycle().isPresent());
            actualCurrentSource.assertCurrent(same);
            authority.requireRetainedCurrent(original,cause,retainedProof,current,same,actualCurrentSource,actualCurrentHead);
            StrictJson.require(same.head().digest().equals(actualCurrentHead.digest()),"retained final replay changed its actual current writer head");
            return new RetainedFinalized(this,cause,replayed,original,retainedProof,current,actualCurrentSource,actualCurrentHead);
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("retained finalization remains missing or unqualified: "+invalid.getMessage(),invalid);}
    }
    /** Recheck immediately before the metadata-only finish, under the identical actual writer lease. */
    public void requireRetainedFinalizedCurrent(RetainedFinalized retained,FullSnapshot current,
            ContinuityStorePort.Session same,SourceQualification actualCurrentSource,Head actualCurrentHead)throws IOException {
        Objects.requireNonNull(retained);Objects.requireNonNull(current);Objects.requireNonNull(same);Objects.requireNonNull(actualCurrentSource);Objects.requireNonNull(actualCurrentHead);
        var authority=retainedFinalPort.orElseThrow(()->new IOException("actual retained-finalization Root authority is not installed"));
        StrictJson.require(retained.owner==this&&retained.cause.owner==this&&retained.current==current&&retained.source==actualCurrentSource
                &&retained.head.digest().equals(actualCurrentHead.digest())&&retained.head.state().sequence()==actualCurrentHead.state().sequence()
                &&same.head().digest().equals(actualCurrentHead.digest()),"historical final custody escaped its original actual metadata-finish scope");
        actualCurrentSource.assertCurrent(same);
        var proof=decodeFinalProof(exactMaterial(retained.originals.evidence(),retained.retainedProof,FINAL_PROOF_MAX_BYTES));
        requireRetainedCanonicalLifecycle(retained.cause,retained.originals,retained.retainedProof,proof,same);
        requireRetainedFinalFrame(retained.cause,retained.originals.beforeFinal(),current,retained.originals.canonicalLifecycle().isPresent());
        authority.requireRetainedCurrent(retained.originals,retained.cause,retained.retainedProof,current,same,actualCurrentSource,actualCurrentHead);
        StrictJson.require(java.util.Arrays.equals(exactMaterial(retained.originals.evidence(),retained.retainedProof,FINAL_PROOF_MAX_BYTES),retained.originalProof()),
                "retained final proof drifted before its metadata finish");
        actualCurrentSource.assertCurrent(same);
        StrictJson.require(same.head().digest().equals(actualCurrentHead.digest()),"retained final metadata scope changed writer head");
    }
    public Finalized finalizeAfterReconnectedPendingContinue(ReconnectedCause custody,FullSnapshot current,
            ContinuityStorePort.Session same,SourceQualification source,Head head)throws IOException {
        requireReconnectedCauseCurrent(custody,current,same,source,head);var cause=custody.cause;
        StrictJson.require(custody.purpose()==ContinuityPurpose.PENDING_UI,"historical finalized continuity cannot repeat final UI business");
        var original=Objects.requireNonNull(finalPort.openQualified(cause,current,same,source,head));
        FinalCurrentCheck check=()->{requireReconnectedCauseCurrent(custody,current,same,source,head);
            finalPort.requireCurrent(cause,current,same,source,head,original);};
        var qualified=finalizeUsing(cause,current,same,head,source.proof(),original,causePort,finalPort::openQualifiedModalQuery,check,
                ()->requireReconnectedCauseCurrent(custody,current,same,source,head));
        return new Finalized(cause,qualified.modal(),qualified.currentSnapshot(),qualified.originals(),qualified.originalProof(),Optional.of(custody.continuityBinding()));
    }
    /** Immediately before the real final business CAS, under the same held physical/writer scope. */
    public void requireReconnectedFinalCurrent(ReconnectedCause custody,Finalized finalized,FullSnapshot current,
            ContinuityStorePort.Session same,SourceQualification source,Head head)throws IOException {
        Objects.requireNonNull(finalized);requireReconnectedCauseCurrent(custody,current,same,source,head);
        StrictJson.require(custody.purpose()==ContinuityPurpose.PENDING_UI,"metadata-only continuity cannot submit final business CAS");
        StrictJson.require(finalized.cause==custody.cause&&finalized.currentSnapshot().equals(current.originalEvidence())
                &&finalized.continuityBinding().equals(Optional.of(custody.continuityBinding())),
                "reconnected final result escaped its exact cause/current continuity scope");
        var document=decodeFinalProof(finalized.originalProof());
        StrictJson.require(document.pendingCauseSha256().equals(custody.causeDigest())&&document.writerHeadSha256().equals(head.digest())
                &&document.writerHeadSequence()==head.state().sequence()&&document.actualOrdinarySnapshot().equals(current.originalEvidence())
                &&document.sourceQualification().equals(source.proof()),"reconnected final proof no longer matches its actual current scope");
        finalPort.requireCurrent(custody.cause,current,same,source,head,finalized.originals());
        requireReconnectedCauseCurrent(custody,current,same,source,head);
    }
    public ReconnectedFinalized qualifyRetainedFinalizationReconnected(ReconnectedCause custody,ExactRef retainedProof,FullSnapshot current,
            ContinuityStorePort.Session same,SourceQualification source,Head head)throws IOException {
        Objects.requireNonNull(retainedProof);requireReconnectedCauseCurrent(custody,current,same,source,head);
        StrictJson.require(custody.purpose()==ContinuityPurpose.FINALIZED_METADATA_ONLY,"retained final metadata requires the exact already-finalized reducer branch");
        var authority=retainedFinalPort.orElseThrow(()->new IOException("actual retained-finalization Root authority is not installed"));
        var continuity=continuityAuthority();var cause=custody.cause;
        try {
            var original=Objects.requireNonNull(authority.openRetainedQualified(cause,retainedProof,current,same,source,head));
            byte[] raw=exactMaterial(original.evidence(),retainedProof,FINAL_PROOF_MAX_BYTES);var document=decodeFinalProof(raw);
            var recordedHead=same.requireHistoricalHead(document.writerHeadSequence(),document.writerHeadSha256());
            StrictJson.require(recordedHead.digest().equals(original.beforeFinalHead().digest())
                    &&recordedHead.state().sequence()==original.beforeFinalHead().state().sequence()&&recordedHead.state().sequence()<=head.state().sequence()
                    &&document.pendingCauseSha256().equals(cause.causeDigest())
                    &&(document.sourceQualification().isPresent()==original.originalSourceQualification().isPresent()
                        &&document.sourceQualification().equals(original.originalSourceQualification())),
                    "reconnected final replay lacks the genuine predecessor head/cause/source original");
            Optional<ContinuityOriginals> historical=sameTransport(original.beforeFinal(),cause)?Optional.empty():Optional.of(Objects.requireNonNull(
                    continuity.openHistoricalFinalQualified(custody.continuity,cause,custody.retainedProof,original,current,same,source,head)));
            FinalCurrentCheck check=()->{
                requireReconnectedCauseCurrent(custody,current,same,source,head);
                requireHistoricalFinalContinuity(custody,historical,original,current,same,source,head);
                authority.requireRetainedCurrent(original,cause,retainedProof,current,same,source,head);
            };
            var replayed=finalizeUsing(cause,original.beforeFinal(),same,original.beforeFinalHead(),original.originalSourceQualification(),
                    original.originals(),original.evidence(),original.evidence()::openQualifiedModalQuery,check,
                    ()->{requireSameGameSuccessor(cause,original.beforeFinal(),false);requireHistoricalFinalContinuity(custody,historical,original,current,same,source,head);});
            StrictJson.require(java.util.Arrays.equals(raw,replayed.originalProof())&&retainedProof.sha256().equals(replayed.digest()),
                    "reconnected historical finalization did not rederive identical complete final proof");
            requireRetainedCanonicalLifecycle(cause,original,retainedProof,document,same);
            requireRetainedFinalFrameSameGame(cause,original.beforeFinal(),current,original.canonicalLifecycle().isPresent());check.requireCurrent();
            var retained=new RetainedFinalized(this,cause,replayed,original,retainedProof,current,source,head);
            return new ReconnectedFinalized(this,custody,retained,historical);
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("same-Game retained finalization remains unqualified: "+invalid.getMessage(),invalid);}
    }
    public void requireReconnectedFinalizedCurrent(ReconnectedFinalized qualified,FullSnapshot current,
            ContinuityStorePort.Session same,SourceQualification source,Head head)throws IOException {
        Objects.requireNonNull(qualified);StrictJson.require(qualified.owner==this,"reconnected final custody belongs to another Root authority");
        requireReconnectedCauseCurrent(qualified.custody,current,same,source,head);
        var retained=qualified.retained;var cause=retained.cause;
        var authority=retainedFinalPort.orElseThrow(()->new IOException("actual retained-finalization Root authority is not installed"));
        StrictJson.require(retained.owner==this&&retained.current==current&&retained.source==source&&retained.head.digest().equals(head.digest())
                &&retained.head.state().sequence()==head.state().sequence(),"reconnected final custody escaped the original actual metadata-finish scope");
        var document=decodeFinalProof(exactMaterial(retained.originals.evidence(),retained.retainedProof,FINAL_PROOF_MAX_BYTES));
        requireHistoricalFinalContinuity(qualified.custody,qualified.historicalContinuity,retained.originals,current,same,source,head);
        requireRetainedCanonicalLifecycle(cause,retained.originals,retained.retainedProof,document,same);
        requireRetainedFinalFrameSameGame(cause,retained.originals.beforeFinal(),current,retained.originals.canonicalLifecycle().isPresent());
        authority.requireRetainedCurrent(retained.originals,cause,retained.retainedProof,current,same,source,head);
        StrictJson.require(java.util.Arrays.equals(exactMaterial(retained.originals.evidence(),retained.retainedProof,FINAL_PROOF_MAX_BYTES),retained.originalProof()),
                "reconnected retained final proof changed before metadata finish");
        requireReconnectedCauseCurrent(qualified.custody,current,same,source,head);
    }
    private void requireHistoricalFinalContinuity(ReconnectedCause custody,Optional<ContinuityOriginals> historical,
            RetainedFinalizationOriginals original,FullSnapshot current,ContinuityStorePort.Session same,SourceQualification source,Head head)throws IOException {
        if(sameTransport(original.beforeFinal(),custody.cause)) {
            StrictJson.require(historical.isEmpty(),"original same-connection final replay cannot invent a rebind");return;
        }
        var exact=historical.orElseThrow(()->new IOException("historical reconnected finalization lacks its own canonical continuity original"));
        StrictJson.require(exact.purpose()==ContinuityPurpose.PENDING_UI,"historical final replay requires its original pending UI reducer scope");
        var authority=continuityAuthority();
        requireContinuityBinding(authority,exact,custody.cause,custody.retainedProof,original.beforeFinal(),original.originalSourceQualification(),same,original.beforeFinalHead(),ContinuityPhase.CANONICAL_HISTORICAL);
        authority.requireHistoricalFinalCurrent(exact,custody.continuity,custody.cause,custody.retainedProof,original,current,same,source,head);
    }
    private static void requireRetainedCanonicalLifecycle(PendingCause cause,RetainedFinalizationOriginals originals,
            ExactRef retainedProof,FinalProofDocument original,ContinuityStorePort.Session same)throws IOException {
        if(originals.canonicalLifecycle().isEmpty())return;
        var actual=originals.canonicalLifecycle().orElseThrow();var proof=actual.proof();proof.validateParent(cause.parent);
        StrictJson.require(proof.kind()==org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR
                &&proof.originalEvidence().contains(retainedProof)
                &&proof.originalEvidence().contains(originals.canonicalFinalizationDomain())
                &&proof.originalEvidence().contains(original.canonicalPublication())
                &&proof.originalEvidence().contains(actual.canonicalEvent()),
                "version+2 requires the same Continue parent and exact finalization/domain/publication/canonical event originals");
        var pin=same.head().documents().stream().filter(value->value.reference().equals(actual.canonicalEvent())).findFirst()
                .orElseThrow(()->new IOException("canonical final lifecycle event is absent from the actual writer head"));
        same.verifyPin(pin);
        // The actual Root port additionally calls the sole Save recorded-metadata/reducer verifier.
        // This shared M3 class does not duplicate that wire schema or infer its phase from JSON DATA.
    }
    private static void requireRetainedFinalFrame(PendingCause cause,FullSnapshot before,FullSnapshot current,boolean lifecycleMetadataCommitted) {
        var old=before.actual().session();var now=current.actual().session();
        StrictJson.require(now.sessionId().equals(old.sessionId())&&now.connectionGeneration().equals(old.connectionGeneration()),
                "retained finalization requires the same exact session and connection");
        requireRetainedFinalFrameSameGame(cause,before,current,lifecycleMetadataCommitted);
    }
    private static void requireRetainedFinalFrameSameGame(PendingCause cause,FullSnapshot before,FullSnapshot current,boolean lifecycleMetadataCommitted) {
        var old=before.actual().session();var now=current.actual().session();var prior=before.facts().driver().session();var after=current.facts().driver().session();
        StrictJson.require(now.machineId().equals(old.machineId())&&now.game().equals(old.game())&&current.facts().transport().equals(now)
                &&before.facts().source().equals(cause.before.source())&&current.facts().source().equals(before.facts().source())
                &&prior.actorId().intValueExact()==cause.successor&&after.actorId().equals(prior.actorId())
                &&after.episodeRunId().equals(prior.episodeRunId())&&!after.episodeRunId().equals(cause.oldEpisodeRunId())
                &&before.facts().episodeEpoch()==Math.addExact(cause.episodeEpoch(),1)&&current.facts().episodeEpoch()==before.facts().episodeEpoch()
                &&current.facts().driverVersion()==Math.addExact(before.facts().driverVersion(),lifecycleMetadataCommitted?2:1)
                &&!current.actual().observedAt().isBefore(before.actual().observedAt()),
                "retained finalization requires exact version+1 business CAS or verified version+2 metadata, with the same physical/source/session/connection successor");
        PendingSameGameContinuity.requireRevisionContinuation(revisionFrame(before),revisionFrame(current));
        var projected=new DriverObservationAssembler().projectFull(current.actual(),current.facts(),current.originalEvidence());
        StrictJson.require(projected.semantic().equals(current.semantic())&&projected.fullBindingSha256().equals(current.fullBindingSha256()),
                "retained final current physical frame differs from the sole full native/Driver projection");
        var semantic=OpportunityJson.toNode(current.semantic());var player=required(semantic,"played_character");StrictJson.trueValue(required(player,"alive"));
        StrictJson.require(StrictJson.integer(required(player,"character_id"),1,Integer.MAX_VALUE)==cause.successor
                &&required(semantic,"one_life_terminal_reason").isNull()
                &&StrictJson.integer(required(semantic,"date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE)
                    >=StrictJson.integer(required(OpportunityJson.toNode(before.semantic()),"date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE),
                "retained final current actor/terminal/date does not retain the historical successor");
        // Current EVENT/estate/readiness are not supplied by this historical metadata-only token.
        // Their original final-UI/date/estate qualification is replayed unchanged below, at beforeFinal.
    }
    private static void requireFinalMaterials(OriginalReader reader,FinalOriginals originals,FullSnapshot current)throws IOException {
        var material=originals.materials();var read=material.currentRootRead();
        StrictJson.require(read.request().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay,
                "ordinary final ROOT read requires its genuine Gameplay origin");
        var origin=read.request().origin().requireGameplay();
        var transport=current.actual().session();var driver=current.facts().driver().session();var frame=origin.frame();
        StrictJson.require(read.request().source().equals(current.facts().source())&&read.request().sessionId().equals(transport.sessionId())
                &&origin.machineId().equals(transport.machineId())&&origin.game().equals(transport.game())
                &&frame.identity().player().equals(driver.actorId())&&frame.episodeRunId().equals(driver.episodeRunId())
                &&frame.snapshotId().equals(current.actual().snapshotId())&&frame.revision().equals(current.facts().publicRevision())
                &&frame.identity().nativeRevision().equals(current.actual().nativeRevision())
                &&frame.identity().dateRaw().equals(BigInteger.valueOf(originals.frame().dateRaw()))
                &&read.before().binding().connectionGeneration().equals(transport.connectionGeneration())
                &&read.after().binding().connectionGeneration().equals(transport.connectionGeneration()),
                "retained final ROOT receipt differs from the actual same ordinary pre-business-CAS frame");
        exactMaterial(reader,material.rootReadReference(),RawJson.MAXIMUM_BYTES);
        var rawRoot=exact(reader,originals.currentRootResult());
        StrictJson.require(read.original().originalResultToken().isPresent()
                &&java.util.Arrays.equals(read.original().originalResultToken().orElseThrow().bytes(),rawRoot),
                "retained final ROOT token differs from its exact original read");
        var knownRaw=DriverSnapshotFacts.originalKnownJson(exactMaterial(reader,material.originalKnown(),DriverSnapshotFacts.MAX_ORIGINAL_BYTES));
        var known=DriverSnapshotFacts.decodeKnownOriginal(knownRaw,material.actualKnown().observation());
        StrictJson.require(java.util.Arrays.equals(DriverSnapshotFacts.encodeKnownOriginal(known).bytes(),DriverSnapshotFacts.encodeKnownOriginal(material.actualKnown()).bytes())
                &&known.stamp().driverVersion()==current.facts().driverVersion()&&known.stamp().episodeEpoch()==current.facts().episodeEpoch()
                &&java.util.Arrays.equals(known.driver().encode(),current.facts().driver().encode()),
                "final Known originals must preserve all seven actual slots and this exact full Driver/version/epoch");
        StrictJson.require(material.actualObservation().equals(current.facts().semanticFactsEvidence()),
                "final snapshot observation is not the actual full-frame producer manifest");
        exactMaterial(reader,material.actualObservation(),RawJson.MAXIMUM_BYTES);
        StrictJson.require(java.util.Arrays.equals(exactMaterial(reader,material.originalSemantic(),FullJsonTree.MAXIMUM_BYTES),DriverJson.encode(current.semantic())),
                "final complete semantic original differs from the actual pre-business-CAS FullSnapshot");
        var projected=new DriverObservationAssembler().projectFull(current.actual(),current.facts(),current.originalEvidence());
        StrictJson.require(projected.semantic().equals(current.semantic())&&projected.fullBindingSha256().equals(current.fullBindingSha256()),
                "historical final FullSnapshot must replay through the sole complete native/Driver projection");
    }
    public Finalized finalizeAfterPendingContinue(PendingCause cause,FullSnapshot current,ContinuityStorePort.Session borrowed,
            SourceQualification source,Head head)throws IOException {
        Objects.requireNonNull(cause);Objects.requireNonNull(current);Objects.requireNonNull(borrowed);Objects.requireNonNull(source);Objects.requireNonNull(head);
        try {
            source.assertCurrent(borrowed);
            FinalOriginals original=Objects.requireNonNull(finalPort.openQualified(cause,current,borrowed,source,head));
            return finalizeUsing(cause,current,borrowed,head,source.proof(),original,causePort,
                    finalPort::openQualifiedModalQuery,()->{source.assertCurrent(borrowed);finalPort.requireCurrent(cause,current,borrowed,source,head,original);});
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("post-Continue finalization remains unqualified: "+invalid.getMessage(),invalid);}
    }
    @FunctionalInterface private interface FinalModalQuery {
        PendingModalClearance.SceneQuery open(Packet packet,ContinuityStorePort.Session same)throws IOException;
    }
    @FunctionalInterface private interface FinalCurrentCheck {void requireCurrent()throws IOException;}
    /** The original UI/date/estate algorithm, shared by live issuance and qualified historical replay. */
    private Finalized finalizeUsing(PendingCause cause,FullSnapshot current,ContinuityStorePort.Session borrowed,
            Head head,Optional<ExactRef> sourceQualification,FinalOriginals original,OriginalReader reader,
            FinalModalQuery modalQueries,FinalCurrentCheck check)throws IOException {
        return finalizeUsing(cause,current,borrowed,head,sourceQualification,original,reader,modalQueries,check,()->{
            var old=cause.before.actual().session();var transport=current.actual().session();var driver=current.facts().driver().session();
            StrictJson.require(transport.machineId().equals(old.machineId())&&transport.game().equals(old.game())&&transport.sessionId().equals(old.sessionId())
                    &&transport.connectionGeneration().equals(old.connectionGeneration())&&current.facts().source().equals(cause.before.source())
                    &&driver.actorId().intValueExact()==cause.successor&&!driver.episodeRunId().equals(cause.oldEpisodeRunId())
                    &&current.facts().episodeEpoch()==Math.addExact(cause.episodeEpoch(),1)&&current.facts().driverVersion()>cause.driverVersion(),
                    "actual ordinary successor must be the sole same-source canonical new episode, without reconnect alias");
        });
    }
    private Finalized finalizeUsing(PendingCause cause,FullSnapshot current,ContinuityStorePort.Session borrowed,
            Head head,Optional<ExactRef> sourceQualification,FinalOriginals original,OriginalReader reader,
            FinalModalQuery modalQueries,FinalCurrentCheck check,FinalCurrentCheck transportCheck)throws IOException {
        try{
            StrictJson.require(cause.owner==this,"pending cause belongs to a different private authority");check.requireCurrent();
            transportCheck.requireCurrent();var transport=current.actual().session();var driver=current.facts().driver().session();
            JsonNode semantic=OpportunityJson.toNode(current.semantic()),player=required(semantic,"played_character");StrictJson.trueValue(required(player,"alive"));
            StrictJson.require(StrictJson.integer(required(player,"character_id"),1,Integer.MAX_VALUE)==cause.successor
                    &&required(semantic,"one_life_terminal_reason").isNull(),"postcommit actual ordinary successor required");
            StrictJson.require(required(semantic,"active_event").isNull()&&required(semantic,"pending_character_interaction").isNull(),"final natural UI requires actual event and interaction resolution; modal clearance alone is insufficient");
            if(semantic.has("one_life_terminal")){JsonNode terminal=semantic.get("one_life_terminal");StrictJson.require(terminal.isBoolean()&&!terminal.booleanValue(),"postcommit terminal flag must be false");}
            Frame now=original.frame();StrictJson.require(now.actorCharacterId()==cause.successor
                    &&now.publicRevision().equals(current.facts().publicRevision())&&now.nativeRevision().equals(current.actual().nativeRevision())
                    &&now.snapshotId().equals(current.actual().snapshotId())&&now.dateRaw()>=cause.before.dateRaw().intValueExact(),
                    "post-Continue UI finalization must retain actual current frame and nonregressing original date");
            Session session=original.session();StrictJson.require(session.machineId().equals(transport.machineId())&&session.sessionId().equals(transport.sessionId())
                    &&session.game().pid()==transport.game().pid()&&session.game().creationFiletime().equals(transport.game().creationFiletime().value().toString())
                    &&session.connectionGeneration().equals(transport.connectionGeneration().toString())&&session.episodeRunId().equals(driver.episodeRunId())
                    &&session.executable().equals(cause.originals.originals().session().executable()),"final UI originals belong to another physical source/new episode");
            requireFinalMaterials(reader,original,current);
            var estate=SuccessionNativeEstate12004.observeCurrentEpisode(exact(reader,original.currentRootResult()),DriverJson.encode(current.semantic()));
            StrictJson.require(estate.snapshot().frame().revision().equals(now.publicRevision())&&estate.snapshot().frame().nativeRevision().equals(now.nativeRevision())
                    &&estate.snapshot().frame().snapshotId().equals(now.snapshotId())&&estate.snapshot().frame().dateRaw()==now.dateRaw()
                    &&estate.snapshot().episodeRunId().equals(driver.episodeRunId())&&estate.snapshot().actor().characterId()==cause.successor,"current ROOT estate must bind actual new ordinary episode");
            var expected=new TreeSet<Integer>(cause.originals.estate().comparison().matchedInheritedTitleIds());expected.addAll(cause.originals.estate().comparison().observedAdditionalSuccessorTitleIds());
            var observed=new TreeSet<Integer>();for(var title:estate.estate().titleRows())observed.add(title.title().titleId());
            StrictJson.require(expected.equals(observed),"actual successor-owned estate changed during UI-only finalization");
            var finalBinding=new NativeTimelineBlocker12004.BoundFrame(session,now,NativeTimelineBlocker12004.Scene.fromSnapshot(semantic));
            var first=query(original.initialTimeline(),session,reader);String clearance;
            if(original.close().isEmpty()){StrictJson.require(first.context().clearedObserved()&&NativeTimelineBlocker12004.sameContinuation(first.binding(),finalBinding),"actual new episode UI is not already clear");clearance="already_clear";}
            else{Packet close=original.close().orElseThrow();StrictJson.require(original.verifiedDateAdvance().isPresent()&&now.dateRaw()>close.actualFrame().dateRaw(),"once-Close requires actual same-successor date advance, qualified by RootFinalPort");var submitted=NativeTimelineBlocker12004.parseClose(exact(reader,close.original()),close.original(),binding(close,session),close.requestId());
                var captured=new ArrayList<PendingModalClearance.SceneQuery>();
                for(Packet packet:original.postqueries()){
                    var next=query(packet,session,reader);var actual=Objects.requireNonNull(modalQueries.open(packet,borrowed));var verified=actual.query();
                    StrictJson.require(verified.original().equals(next.original())&&verified.requestId().equals(next.requestId())
                            &&verified.binding().equals(next.binding())&&verified.sequence().equals(next.sequence())
                            &&verified.observationRevision().equals(next.observationRevision())&&verified.context().equals(next.context()),
                            "private Root modal read differs from the exact finalization packet");captured.add(actual);
                }
                var modal=PendingModalClearance.inspect(first,submitted,captured);
                StrictJson.require(modal.state()==NativeTimelineBlocker12004.ClearanceState.CLEARED_OBSERVED,"once-Close ACK is not independent modal clearance before actual date advance");
                var last=captured.getLast().query();BigInteger sequence=last.sequence(),revision=last.observationRevision();
                var afterAdvance=query(original.finalTimelineAfterDateAdvance().orElseThrow(),session,reader);
                StrictJson.require(afterAdvance.context().clearedObserved()&&afterAdvance.sequence().compareTo(sequence)>0&&afterAdvance.observationRevision().compareTo(revision)>0&&NativeTimelineBlocker12004.sameContinuation(afterAdvance.binding(),finalBinding),"actual later date must retain a fresh independently clear new-episode surface");clearance="legal_close_then_actual_date_advance_observed_clear";}
            // Root verifies these are the actual pending publication originals, not synthetic reference-shaped DATA.
            // Their large material domains are checked by the actual RootFinalPort; do not parse full Driver with a UI packet budget.
            check.requireCurrent();
            var material=original.materials();
            var proof=new FinalProofDocument(transport.machineId(),current.actual().observedAt(),cause.causeDigest(),
                    head.digest(),head.state().sequence(),driver.episodeRunId(),cause.successor,FinalClearance.parse(clearance),now.dateRaw(),
                    current.originalEvidence(),material.actualObservation(),original.currentRootResult(),material.rootReadReference(),material.originalKnown(),material.originalSemantic(),
                    original.pendingContinueReceipt(),original.pendingContinueDriver(),original.canonicalPublicationProof(),sourceQualification,
                    original.initialTimeline().original(),original.postqueries().stream().map(Packet::original).toList(),
                    original.close().map(Packet::original),original.verifiedDateAdvance(),original.finalTimelineAfterDateAdvance().map(Packet::original));
            return new Finalized(cause,clearance,current.originalEvidence(),original,encodeFinalProof(proof));
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("post-Continue finalization remains unqualified: "+invalid.getMessage(),invalid);}
    }
    private NativeTimelineBlocker12004.Query query(Packet packet,Session session,OriginalReader reader)throws IOException{return NativeTimelineBlocker12004.parseQuery(exact(reader,packet.original()),packet.original(),binding(packet,session),packet.requestId());}
    private static NativeTimelineBlocker12004.BoundFrame binding(Packet packet,Session session){return new NativeTimelineBlocker12004.BoundFrame(session,packet.actualFrame(),packet.actualScene());}
    private byte[] exact(ExactRef ref)throws IOException{return exact(causePort,ref);}
    private static byte[] exact(OriginalReader port,ExactRef ref)throws IOException{return exactMaterial(port,ref,NativeTimelineBlocker12004.MAX_BYTES);}
    private static byte[] exactMaterial(OriginalReader port,ExactRef ref,int maximumBytes)throws IOException{StrictJson.require(ref.bytes()>0&&ref.bytes()<=maximumBytes,"bounded retained original material required");byte[] raw=port.readExact(ref);if(raw==null||raw.length!=ref.bytes()||!G2RetainedNativeSourceProvider.sha256(raw).equals(ref.sha256()))throw new IOException("retained original bytes/SHA changed: "+ref.path());return raw.clone();}
    private static JsonNode required(JsonNode n,String field){StrictJson.require(n!=null&&n.isObject()&&n.has(field),"missing actual field: "+field);return n.get(field);}
}
