package org.xar.ck3.control.nativebridge.capabilities.registry;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CharacterManagerObservation1210.*;

/** Consumer and replay of original manager candidate DATA bytes. No endpoint, live custody or action role.
 * A roster contains manager members only; it cannot establish all living characters or interaction candidates.
 */
public final class CharacterManagerRoster1210 {
    /** Author batch budget, independent of the native manager vector observation limit. */
    public static final int MAX_LOOKUPS = 256;
    private CharacterManagerRoster1210() { }
    public enum Scope { MANAGER_MEMBERS_ONLY }

    public record PacketIdentity(int bytes, String sha256) {
        public PacketIdentity {
            StrictJson.require(bytes > 0 && bytes <= CharacterManagerObservation1210.MAX_PACKET_BYTES,
                    "original candidate packet byte budget exceeded");
            StrictJson.require(sha256 != null && sha256.matches("[0-9a-f]{64}"), "exact original candidate packet digest required");
        }
    }
    /** Only receive() constructs a capture; caller and returned byte arrays cannot mutate its retained input. */
    public static final class Capture {
        private final byte[] original;
        private final PacketIdentity identity;
        private final Observation observation;
        private Capture(byte[] original, PacketIdentity identity, Observation observation) {
            this.original = original; this.identity = identity; this.observation = observation;
        }
        public byte[] original() { return original.clone(); }
        public PacketIdentity identity() { return identity; }
        public Observation observation() { return observation; }
    }
    public record Row(NativeCharacterId requestedId, MemberLookup result) {
        public Row {
            Objects.requireNonNull(requestedId); Objects.requireNonNull(result);
            NativeCharacterId actual;
            if (result instanceof MemberPresent present) actual = present.member().characterId();
            else if (result instanceof MemberAbsent absent) actual = absent.requestedId();
            else if (result instanceof ManagerUnavailable unavailable) actual = unavailable.requestedId();
            else actual = ((FrameMismatch) result).requestedId();
            StrictJson.require(requestedId.equals(actual), "roster result differs from the exact requested full generation");
        }
    }
    /** Request order and repeated requests are retained. Dead rows are not filtered into a living-population claim. */
    public record Roster(PacketIdentity input, Prefix expected, List<Row> rows) {
        public Roster {
            Objects.requireNonNull(input); Objects.requireNonNull(expected); rows = List.copyOf(rows);
            StrictJson.require(rows.size() <= MAX_LOOKUPS, "author roster batch budget exceeded");
        }
        public Scope scope() { return Scope.MANAGER_MEMBERS_ONLY; }
    }

    /** Decode the actual supplied bytes before allowing any lookup; no synthetic observation fallback. */
    public static Capture receive(byte[] original) {
        StrictJson.require(original != null && original.length > 0
                && original.length <= CharacterManagerObservation1210.MAX_PACKET_BYTES, "bounded original manager DATA required");
        byte[] retained = original.clone();
        Observation observation = CharacterManagerObservation1210.decode(retained);
        return new Capture(retained, new PacketIdentity(retained.length, sha256(retained)), observation);
    }
    /** Replay reparses retained original bytes. It neither queries Native nor rewrites a failed observation. */
    public static Capture replay(Capture retained) {
        Objects.requireNonNull(retained);
        Capture replayed = receive(retained.original());
        StrictJson.require(retained.identity().equals(replayed.identity())
                && retained.observation().equals(replayed.observation()), "retained manager DATA replay differs");
        return replayed;
    }
    /** Every result comes from the shared full-generation lookup on this capture's decoded original DATA. */
    public static Roster lookup(Capture captured, Prefix expected, List<NativeCharacterId> requested) {
        Objects.requireNonNull(captured); Objects.requireNonNull(expected);
        List<NativeCharacterId> ids = List.copyOf(requested);
        StrictJson.require(ids.size() <= MAX_LOOKUPS, "author roster batch budget exceeded");
        List<Row> rows = new ArrayList<>(ids.size());
        for (NativeCharacterId id : ids)
            rows.add(new Row(id, CharacterManagerObservation1210.lookup(captured.observation(), expected, id)));
        return new Roster(captured.identity(), expected, rows);
    }
    private static String sha256(byte[] original) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException("SHA-256 unavailable", impossible); }
    }
}
