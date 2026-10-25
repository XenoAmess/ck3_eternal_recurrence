package org.xar.ck3.rrf.qualification;

import java.nio.file.Path;
import java.util.List;
import java.util.Set;
import org.xar.ck3.rrf.Contracts;

/** Explicit source-binding evidence; no execution, build, or game authority. */
public final class SourceQualificationContracts {
    private SourceQualificationContracts() { }
    public enum Chain {
        PUBLIC_CONTROL("public_control"), CASE_HOOKS("case_hooks"), SHARED_HOST("shared_host"),
        SHARED_SDK_DELTA("shared_sdk_delta"), PILGRIMAGE_WIRE_SEAM("pilgrimage_wire_seam"), OTHER_SOURCE_DELTA("other_source_delta");
        private final String wire;
        Chain(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum ProofKind { COMMAND_VALIDATION, COMMAND_SOURCE_EXECUTION, MAVEN_REVIEW, SOURCE_REVIEW }
    public enum Disposition { RAW_EQUAL_PRIOR, SOURCE_PROOF_COVERS }
    public enum Status { SOURCE_BOUND_NOT_LIVE, GAP }
    public record Pin(String path, long bytes, String sha256) {
        public Pin { if (path == null || !Path.of(path).isAbsolute() || bytes < 0) throw new IllegalArgumentException("absolute exact file pin required"); Contracts.digest(sha256); }
    }
    public record Proof(ProofKind kind, Pin receipt) {
        public Proof { if (kind == null || receipt == null) throw new IllegalArgumentException("typed proof required"); }
    }
    public record ChainPlan(Chain chain, Pin previousQualification, List<Proof> proofs) {
        public ChainPlan {
            if (chain == null || previousQualification == null) throw new IllegalArgumentException("chain predecessor required");
            proofs = List.copyOf(proofs); if (proofs.size() > 128) throw new IllegalArgumentException("too many source proofs");
        }
    }
    public record Request(int schemaVersion, String machineId, String repository, String sourceCommit,
                          Pin sourceDelta, Pin classifierProgram, List<ChainPlan> chains, Pin previousHostDelta) {
        public Request {
            Contracts.schema(schemaVersion);
            if (machineId == null || machineId.isBlank() || repository == null || !Path.of(repository).isAbsolute()
                    || sourceCommit == null || !sourceCommit.matches("[a-f0-9]{40}") || sourceDelta == null || classifierProgram == null || previousHostDelta == null) throw new IllegalArgumentException("explicit source qualification identity required");
            chains = List.copyOf(chains);
            if (chains.size() != Chain.values().length || Set.copyOf(chains.stream().map(ChainPlan::chain).toList()).size() != Chain.values().length) throw new IllegalArgumentException("exactly six unique chain plans required");
        }
    }
    public record Relation(String path, Pin current, Disposition disposition, Pin proof) { }
    public record Gap(String chain, String path, String reason) { }
    public record Result(String schema, String machineId, String sourceCommit, String observedAtUtc,
                         Status status, List<Pin> outputs, List<Gap> gaps, boolean testsRunByProducer,
                         boolean nativeRebuilt, boolean gameStarted) {
        public Result { outputs = List.copyOf(outputs); gaps = List.copyOf(gaps); }
    }
}
