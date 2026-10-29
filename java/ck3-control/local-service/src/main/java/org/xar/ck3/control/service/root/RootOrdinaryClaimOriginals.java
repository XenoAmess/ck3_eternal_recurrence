package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ordinary.OrdinaryOnceClaims;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual, bounded legacy-directory producer. Missing/unreadable/changing originals never mean zero claims. */
public final class RootOrdinaryClaimOriginals {
    public static final String LEGACY_SCHEMA = "ck3-ordinary-interaction-once-claim-v1";
    public static final int MAX_FILES = 4096;
    public static final int MAX_FILE_BYTES = 1 << 20;
    public static final long MAX_TOTAL_BYTES = 16L << 20;
    private RootOrdinaryClaimOriginals() { }
    public record Legacy(long gamePid, long actorId, String interactionKey, long recipientId, String requestId, long ordinal) {
        public Legacy {
            StrictJson.require(gamePid > 0 && gamePid <= 0xffff_ffffL && actorId > 0 && actorId <= 0xffff_fffeL
                    && recipientId > 0 && recipientId <= 0xffff_fffeL, "actual legacy full native identities required");
            StrictJson.require(interactionKey != null && interactionKey.matches("[A-Za-z0-9_]{1,128}"), "exact original interaction key required");
            StrictJson.require(requestId != null && requestId.matches("[A-Za-z0-9_.:-]{1,128}") && ordinal >= 0 && ordinal <= 0xffff_ffffL,
                    "actual original ordinary request/ordinal required");
        }
    }
    public static final class Original {
        private final Path path;
        private final SharedSourceFiles.Witness witness;
        private final byte[] bytes;
        private final Legacy legacy;
        private Original(Path path, SharedSourceFiles.Witness witness, byte[] bytes, Legacy legacy) {
            this.path = path; this.witness = witness; this.bytes = bytes.clone(); this.legacy = legacy;
        }
        public Path path() { return path; }
        public SharedSourceFiles.Witness witness() { return witness; }
        public byte[] bytes() { return bytes.clone(); }
        public Legacy legacy() { return legacy; }
        public ExactRef source() { var source = witness.source(); return new ExactRef(source.path(), source.bytes(), source.sha256()); }
    }
    public static final class Captured {
        private final Path directory;
        private final SharedSourceFiles.DirectoryIdentity identity;
        private final List<Path> names;
        private final List<Original> originals;
        private Captured(Path directory, SharedSourceFiles.DirectoryIdentity identity, List<Path> names, List<Original> originals) {
            this.directory = directory; this.identity = identity; this.names = List.copyOf(names); this.originals = List.copyOf(originals);
        }
        public Path directory() { return directory; }
        public SharedSourceFiles.DirectoryIdentity identity() { return identity; }
        public List<Original> originals() { return originals; }
        public void requireUnchanged() throws IOException {
            StrictJson.require(SharedSourceFiles.nativeDirectory(directory).equals(identity) && names(directory).equals(names),
                    "complete original claim directory identity or inventory changed");
            for (Original original : originals) SharedSourceFiles.assertUnchanged(original.witness());
            StrictJson.require(SharedSourceFiles.nativeDirectory(directory).equals(identity) && names(directory).equals(names),
                    "original claim census changed while exact source pins were verified");
        }
        /** Conservative migration: float/null process birth never becomes an exact FILETIME or a releasable Java claim. */
        public OrdinaryOnceClaims.State state(String captureMachineId, List<ExactRef> retainedOriginals) throws IOException {
            retainedOriginals = List.copyOf(retainedOriginals);
            StrictJson.require(retainedOriginals.size() == originals.size(), "every original claim requires its exact retained bytes");
            requireUnchanged(); List<OrdinaryOnceClaims.LegacyBlocker> blockers = new ArrayList<>();
            for (int index = 0; index < originals.size(); index++) {
                Original source = originals.get(index); ExactRef retained = retainedOriginals.get(index);
                StrictJson.require(retained.bytes() == source.bytes.length && retained.sha256().equals(ActionCodec.sha256(source.bytes)),
                        "retained legacy original differs from the complete actual producer");
                Legacy identity = source.legacy;
                blockers.add(new OrdinaryOnceClaims.LegacyBlocker(captureMachineId, identity.gamePid(), identity.actorId(),
                        identity.interactionKey(), identity.recipientId(), retained,
                        "legacy process birth is float/null and original machine is unverified; preserve a conservative capture-machine blocker without exact identity or retry credit"));
            }
            return new OrdinaryOnceClaims.State(captureMachineId, List.of(), List.of(), blockers);
        }
    }
    public static Captured capture(Path actualDirectory) throws IOException {
        Objects.requireNonNull(actualDirectory);
        StrictJson.require(actualDirectory.isAbsolute(), "actual original claim directory must be absolute");
        Path directory = actualDirectory.toAbsolutePath().normalize();
        var directoryIdentity = SharedSourceFiles.nativeDirectory(directory); // Missing directories fail here; never created.
        List<Path> names = names(directory); List<Original> originals = new ArrayList<>(); long total = 0;
        for (Path path : names) {
            long length = Files.size(path);
            StrictJson.require(length > 0 && length <= MAX_FILE_BYTES, "bounded nonempty original claim required");
            total = Math.addExact(total, length); StrictJson.require(total <= MAX_TOTAL_BYTES, "complete original claim input exceeds its finite read bound");
            var witness = SharedSourceFiles.observe(path);
            byte[] bytes;
            try (var input = Files.newInputStream(path, LinkOption.NOFOLLOW_LINKS)) { bytes = input.readNBytes(MAX_FILE_BYTES + 1); }
            StrictJson.require(bytes.length == length && bytes.length == witness.source().bytes()
                    && witness.source().sha256().equals(ActionCodec.sha256(bytes)), "original claim changed during its exact native-identity read");
            SharedSourceFiles.assertUnchanged(witness);
            originals.add(new Original(path, witness, bytes, decodeLegacy(bytes)));
        }
        Captured captured = new Captured(directory, directoryIdentity, names, originals); captured.requireUnchanged(); return captured;
    }
    private static List<Path> names(Path directory) throws IOException {
        List<Path> result = new ArrayList<>();
        try (var children = Files.newDirectoryStream(directory)) {
            for (Path path : children) {
                if (!path.getFileName().toString().toLowerCase(java.util.Locale.ROOT).endsWith(".claim.json")) continue;
                StrictJson.require(Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(path), "ordinary original claim must be a regular non-link file");
                result.add(path.toAbsolutePath().normalize()); StrictJson.require(result.size() <= MAX_FILES, "complete ordinary claim inventory exceeds its finite bound");
            }
        }
        return result.stream().sorted(java.util.Comparator.comparing(Path::toString)).toList();
    }
    public static Legacy decodeLegacy(byte[] original) {
        ObjectNode claim = StrictJson.object(StrictJson.parse(original, MAX_FILE_BYTES), Set.of("schema", "request_id", "binding", "action_identity",
                "claim_ordinal", "host_provenance", "new_intent_lineage", "status"));
        StrictJson.require(LEGACY_SCHEMA.equals(StrictJson.text(claim.get("schema")))
                && "claimed_result_unknown_no_retry".equals(StrictJson.text(claim.get("status"))), "only the actual unresolved original claim schema/status is migratable");
        ObjectNode identity = StrictJson.object(claim.get("action_identity"), Set.of("game_pid", "actor_id", "process_create_time", "interaction_key", "recipient_id", "action"));
        StrictJson.require("initiate_ordinary".equals(StrictJson.text(identity.get("action"))), "legacy original is not an ordinary initiation");
        var birth = identity.get("process_create_time");
        StrictJson.require(birth.isNull() || birth.isNumber() && birth.decimalValue().signum() > 0, "legacy process time is an original positive number or explicit null; it never grants exact identity");
        StrictJson.require(claim.get("binding").isObject(), "actual original claim binding must be preserved as an object");
        StrictJson.require(claim.get("host_provenance").isObject() || claim.get("host_provenance").isNull(), "original host provenance must retain object/null distinction");
        StrictJson.require(claim.get("new_intent_lineage").isObject() || claim.get("new_intent_lineage").isNull(), "original lineage must retain object/null distinction");
        return new Legacy(StrictJson.integer(identity.get("game_pid"), 1, 0xffff_ffffL), StrictJson.integer(identity.get("actor_id"), 1, 0xffff_fffeL),
                StrictJson.text(identity.get("interaction_key")), StrictJson.integer(identity.get("recipient_id"), 1, 0xffff_fffeL),
                StrictJson.text(claim.get("request_id")), StrictJson.integer(claim.get("claim_ordinal"), 0, 0xffff_ffffL));
    }
}
