package org.xar.ck3.control.application.lifecycle;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.regex.Pattern;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.semantic.NativeOneLifeSettlement;

/** The original settlement contract and actual two-read tutorial record producer. No gameplay submission. */
public final class DeathSettlement {
    private DeathSettlement() { }
    public record Ready(BigInteger sourceCharacterId,BigDecimal finalScore,BigInteger recordCandidate,
            boolean recordWritten,byte[] normalized) {
        public Ready {
            java.util.Objects.requireNonNull(sourceCharacterId);java.util.Objects.requireNonNull(finalScore);java.util.Objects.requireNonNull(recordCandidate);
            normalized=normalized.clone();
            var parsed=NativeOneLifeSettlement.decodeNormalized(normalized,FullJsonTree.MAXIMUM_BYTES);
            StrictJson.require(parsed instanceof NativeOneLifeSettlement.Ready,"typed ready settlement must retain its complete normalized ready wire");
            var row=(NativeOneLifeSettlement.Ready)parsed;
            StrictJson.require(sourceCharacterId.equals(row.sourceCharacterId())&&finalScore.compareTo(row.finalScore().decimal())==0
                    &&recordCandidate.equals(row.recordCandidate())&&recordWritten==row.recordWritten(),"typed ready settlement differs from actual normalized wire");
        }
        @Override public byte[] normalized(){return normalized.clone();}
        public NativeOneLifeSettlement.Ready typed() {
            var parsed=NativeOneLifeSettlement.decodeNormalized(normalized,FullJsonTree.MAXIMUM_BYTES);
            if(parsed instanceof NativeOneLifeSettlement.Ready ready)return ready;
            throw new IllegalStateException("immutable Ready lost its validated normalized wire");
        }
        public JsonNode normalizedJson() { return NativeOneLifeSettlement.encode(typed()); }
        public JsonNode scoreJson() { return NativeOneLifeSettlement.encodeScore(typed().finalScore()); }
    }
    public enum PersistenceStatus {
        PERSISTED("persisted"),ZERO_SCORE("not_required_zero_score"),NO_NEW_RECORD("not_required_no_new_record"),UNAVAILABLE("settlement_unavailable");
        private final String wire;PersistenceStatus(String wire){this.wire=wire;}public String wire(){return wire;}
    }
    public record Persistence(PersistenceStatus status,boolean required,Optional<FileWitness> file,List<ExactRef> evidence) {
        public Persistence { java.util.Objects.requireNonNull(status);file=java.util.Objects.requireNonNull(file);evidence=List.copyOf(evidence);
            StrictJson.require(required==(status==PersistenceStatus.PERSISTED)&&file.isPresent()==required
                    &&(required?evidence.equals(List.of(file.orElseThrow().reference())):evidence.isEmpty()),"actual tutorial persistence scope differs"); }
    }
    public static Optional<Ready> normalize(JsonNode nativeValue) {
        var parsed=NativeOneLifeSettlement.decodeNative(nativeValue==null?com.fasterxml.jackson.databind.node.MissingNode.getInstance():nativeValue);
        return ready(parsed);
    }
    /** Consume already normalized SEM/public/archive DATA without treating ratio floats as fresh scalar input. */
    public static Optional<Ready> fromNormalized(JsonNode normalizedValue) {
        return ready(NativeOneLifeSettlement.decodeNormalized(normalizedValue));
    }
    private static Optional<Ready> ready(NativeOneLifeSettlement.State parsed) {
        if(!(parsed instanceof NativeOneLifeSettlement.Ready ready))return Optional.empty();
        return Optional.of(new Ready(ready.sourceCharacterId(),ready.finalScore().decimal(),ready.recordCandidate(),ready.recordWritten(),
                NativeOneLifeSettlement.encode(ready,FullJsonTree.MAXIMUM_BYTES)));
    }
    public static BigDecimal fixedScore(JsonNode value) {
        return NativeOneLifeSettlement.normalizeScore(value,"score").decimal();
    }
    public static Persistence awaitPersistence(Ready settlement,CheckpointFiles files,Path originalTutorial,Instant deadline,Clock clock)throws IOException,InterruptedException {
        if(settlement.recordCandidate().signum()==0)return new Persistence(PersistenceStatus.ZERO_SCORE,false,Optional.empty(),List.of());
        if(!settlement.recordWritten())return new Persistence(PersistenceStatus.NO_NEW_RECORD,false,Optional.empty(),List.of());
        FileWitness prior=null;String lesson="xar_hs_ge_"+settlement.recordCandidate();
        while(clock.instant().isBefore(deadline)) {
            Optional<FileWitness> found=files.observe(originalTutorial);
            if(found.isPresent()) {
                FileWitness actual=found.orElseThrow();String body=new String(files.read(actual,4<<20),StandardCharsets.UTF_8);
                if(lessons(body).contains(lesson)) {
                    if(prior!=null&&prior.equals(actual))return new Persistence(PersistenceStatus.PERSISTED,true,Optional.of(actual),List.of(actual.reference()));
                    prior=actual;
                }else prior=null;
            }else prior=null;
            Thread.sleep(Math.min(50,Math.max(1,java.time.Duration.between(clock.instant(),deadline).toMillis())));
        }
        throw new IOException("new settlement record was not proved by two identical actual tutorial reads before deadline");
    }
    public static java.util.Set<String> lessons(String raw) {
        String text=raw.startsWith("\ufeff")?raw.substring(1):raw;
        var block=Pattern.compile("\\bcompleted_lessons\\s*=\\s*\\{(?<body>.*?)\\}",Pattern.DOTALL).matcher(text);
        java.util.Set<String> result=new java.util.HashSet<>();
        while(block.find()) {
            var token=Pattern.compile("\"([^\"\\r\\n]*)\"|([A-Za-z0-9_.:-]+)").matcher(block.group("body"));
            while(token.find())result.add(token.group(1)==null?token.group(2):token.group(1));
        }
        return java.util.Set.copyOf(result);
    }
}
