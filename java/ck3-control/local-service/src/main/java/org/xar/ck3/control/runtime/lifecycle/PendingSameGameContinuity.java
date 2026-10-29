package org.xar.ck3.control.runtime.lifecycle;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.readiness.NativeSourceProofDocument;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Canonical retained/current observation DATA. Decoding never issues continuity custody. */
public final class PendingSameGameContinuity {
    public static final String SCHEMA="xar.java.pending-same-game-continuity/v1";
    public static final int MAX_BYTES=65_536;
    private static final BigInteger U64_MAX=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final Set<String> FIELDS=Set.of("schema","machine_id","observed_at_utc","game_pid",
            "game_creation_filetime_decimal","game_executable","retained_cause_proof","original_session_id",
            "original_connection_generation_decimal","current_session_id","current_connection_generation_decimal",
            "historical_native",
            "current_native","current_known","current_observation","successor_character_id","successor_episode_run_id",
            "episode_epoch","driver_version","writer_head_sha256","writer_head_sequence");
    private PendingSameGameContinuity() { }

    /** DATA for the original continuation rule; public revision belongs to one exact transport. */
    public record RevisionFrame(String sessionId,String connectionGenerationDecimal,BigInteger publicRevision,
            BigInteger nativeRevision,int dateRaw) {
        public RevisionFrame {
            StrictJson.text(sessionId);decimal(connectionGenerationDecimal);
            StrictJson.require(Objects.requireNonNull(publicRevision).signum()>=0&&Objects.requireNonNull(nativeRevision).signum()>=0,
                    "nonnegative actual public/native revisions required");
        }
    }
    public static void requireRevisionContinuation(RevisionFrame before,RevisionFrame current) {
        Objects.requireNonNull(before);Objects.requireNonNull(current);
        boolean same=before.sessionId().equals(current.sessionId())
                &&before.connectionGenerationDecimal().equals(current.connectionGenerationDecimal());
        StrictJson.require((!same||current.publicRevision().compareTo(before.publicRevision())>=0)
                &&current.nativeRevision().compareTo(before.nativeRevision())>=0&&current.dateRaw()>=before.dateRaw(),
                "public revision must not regress within one transport; native revision and date must not regress across any transport");
    }

    public record Binding(String machineId,Instant observedAtUtc,int gamePid,String gameCreationFiletimeDecimal,
            ExactRef gameExecutable,ExactRef retainedCauseProof,String originalSessionId,String originalConnectionGenerationDecimal,
            String currentSessionId,String currentConnectionGenerationDecimal,Optional<ExactRef> originalSourceQualification,
            Optional<ExactRef> currentSourceQualification,Optional<ExactRef> sourceEpochManifest,ExactRef historicalNative,ExactRef currentNative,
            ExactRef currentKnown,ExactRef currentObservation,int successorCharacterId,String successorEpisodeRunId,
            long episodeEpoch,long driverVersion,String writerHeadSha256,long writerHeadSequence) {
        public Binding {
            StrictJson.text(machineId);Objects.requireNonNull(observedAtUtc);StrictJson.utc(observedAtUtc.toString());
            StrictJson.require(gamePid>0&&successorCharacterId>0,"actual positive OS pid and successor required");
            decimal(gameCreationFiletimeDecimal);decimal(originalConnectionGenerationDecimal);decimal(currentConnectionGenerationDecimal);
            StrictJson.text(originalSessionId);StrictJson.text(currentSessionId);StrictJson.text(successorEpisodeRunId);
            StrictJson.safe(episodeEpoch,0);StrictJson.safe(driverVersion,0);StrictJson.safe(writerHeadSequence,0);
            StrictJson.require(writerHeadSha256!=null&&writerHeadSha256.matches("[0-9a-f]{64}"),"actual writer digest required");
            for(ExactRef ref:List.of(gameExecutable,retainedCauseProof,historicalNative,currentNative,currentKnown,currentObservation))
                StrictJson.require(Objects.requireNonNull(ref).bytes()>0,"nonempty actual retained/current original required");
            Objects.requireNonNull(originalSourceQualification);Objects.requireNonNull(currentSourceQualification);Objects.requireNonNull(sourceEpochManifest);
            originalSourceQualification.ifPresent(ref->StrictJson.require(ref.bytes()>0,"nonempty actual original source qualification required"));
            currentSourceQualification.ifPresent(ref->StrictJson.require(ref.bytes()>0,"nonempty actual current source qualification required"));
            sourceEpochManifest.ifPresent(ref->StrictJson.require(ref.bytes()>0,"nonempty actual source epoch manifest required"));
        }
        public List<ExactRef> materialReferences() {
            // Executable and epoch are software provenance checked through v3 Witnesses, not copied game blobs.
            var refs=new java.util.ArrayList<>(List.of(retainedCauseProof,historicalNative,currentNative,currentKnown,currentObservation));
            originalSourceQualification.ifPresent(refs::add);
            currentSourceQualification.ifPresent(refs::add);
            sourceEpochManifest.ifPresent(refs::add);
            return refs.stream().distinct().toList();
        }
    }
    public static byte[] encode(Binding value) {
        Objects.requireNonNull(value);
        ObjectNode out=StrictJson.object().put("schema",SCHEMA).put("machine_id",value.machineId())
                .put("observed_at_utc",value.observedAtUtc().toString()).put("game_pid",value.gamePid())
                .put("game_creation_filetime_decimal",value.gameCreationFiletimeDecimal())
                .put("original_session_id",value.originalSessionId()).put("original_connection_generation_decimal",value.originalConnectionGenerationDecimal())
                .put("current_session_id",value.currentSessionId()).put("current_connection_generation_decimal",value.currentConnectionGenerationDecimal())
                .put("successor_character_id",value.successorCharacterId()).put("successor_episode_run_id",value.successorEpisodeRunId())
                .put("episode_epoch",value.episodeEpoch()).put("driver_version",value.driverVersion())
                .put("writer_head_sha256",value.writerHeadSha256()).put("writer_head_sequence",value.writerHeadSequence());
        out.set("game_executable",value.gameExecutable().toJson());out.set("retained_cause_proof",value.retainedCauseProof().toJson());
        out.set("original_source_qualification",ExactRef.optionalToJson(value.originalSourceQualification()));
        out.set("current_source_qualification",ExactRef.optionalToJson(value.currentSourceQualification()));
        out.set("source_epoch_manifest",ExactRef.optionalToJson(value.sourceEpochManifest()));
        out.set("historical_native",value.historicalNative().toJson());
        out.set("current_native",value.currentNative().toJson());out.set("current_known",value.currentKnown().toJson());out.set("current_observation",value.currentObservation().toJson());
        return StrictJson.canonical(out,MAX_BYTES);
    }
    public static Binding decode(byte[] original) {
        ObjectNode row=StrictJson.object(StrictJson.parse(original,MAX_BYTES),FIELDS,Set.of("original_source_qualification","current_source_qualification","source_epoch_manifest"));
        StrictJson.require(SCHEMA.equals(text(row,"schema")),"canonical same-Game continuity DATA v1 required");
        return new Binding(text(row,"machine_id"),Instant.parse(StrictJson.utc(text(row,"observed_at_utc"))),
                (int)StrictJson.integer(row.get("game_pid"),1,Integer.MAX_VALUE),text(row,"game_creation_filetime_decimal"),
                ref(row,"game_executable"),ref(row,"retained_cause_proof"),text(row,"original_session_id"),
                text(row,"original_connection_generation_decimal"),text(row,"current_session_id"),
                text(row,"current_connection_generation_decimal"),
                ExactRef.optionalFromJson(row.get("original_source_qualification")),ExactRef.optionalFromJson(row.get("current_source_qualification")),ExactRef.optionalFromJson(row.get("source_epoch_manifest")),
                ref(row,"historical_native"),ref(row,"current_native"),ref(row,"current_known"),ref(row,"current_observation"),
                (int)StrictJson.integer(row.get("successor_character_id"),1,Integer.MAX_VALUE),text(row,"successor_episode_run_id"),
                integer(row,"episode_epoch"),integer(row,"driver_version"),text(row,"writer_head_sha256"),integer(row,"writer_head_sequence"));
    }
    /** Each source document binds its own actual transport. Neither session is treated as an alias. */
    public static void requireSourceContinuity(Binding binding,NativeSourceProofDocument before,NativeSourceProofDocument after) {
        Objects.requireNonNull(binding);Objects.requireNonNull(before);Objects.requireNonNull(after);
        StrictJson.require(before.machineId().equals(binding.machineId())&&after.machineId().equals(binding.machineId())
                &&before.sessionId().equals(binding.originalSessionId())&&after.sessionId().equals(binding.currentSessionId())
                &&before.mode()==after.mode()&&before.hostConfiguration().equals(after.hostConfiguration())
                &&before.source().equals(after.source())&&before.ownerSourceEpoch().equals(after.ownerSourceEpoch())
                &&before.gameExecutable().equals(binding.gameExecutable())&&after.gameExecutable().equals(binding.gameExecutable())
                &&before.completeEvidenceClosure().equals(after.completeEvidenceClosure())&&before.liveWitnesses().size()==after.liveWitnesses().size()
                &&!Instant.parse(before.observedAtUtc()).isAfter(Instant.parse(after.observedAtUtc())),
                "retained/current exact transport, immutable source epoch or observation order differs");
        binding.sourceEpochManifest().ifPresent(manifest->StrictJson.require(before.sourceEpochManifest().equals(manifest)&&after.sourceEpochManifest().equals(manifest),
                "retained/current source epoch manifest differs from binding"));
        for(int index=0;index<before.liveWitnesses().size();index++)
            StrictJson.require(before.liveWitnesses().get(index).sameImmutableFile(after.liveWitnesses().get(index)),
                    "retained/current original source FileID, content, creation or write time differs");
    }
    private static String text(ObjectNode row,String field){return StrictJson.text(row.get(field));}
    private static ExactRef ref(ObjectNode row,String field){return ExactRef.fromJson(row.get(field));}
    private static long integer(ObjectNode row,String field){return StrictJson.integer(row.get(field),0,StrictJson.MAX_SAFE_INTEGER);}
    private static void decimal(String value) {
        StrictJson.require(value!=null&&value.length()<=20&&value.matches("0|[1-9][0-9]*")&&new BigInteger(value).compareTo(U64_MAX)<=0,
                "canonical unsigned 64-bit decimal string required");
    }
}