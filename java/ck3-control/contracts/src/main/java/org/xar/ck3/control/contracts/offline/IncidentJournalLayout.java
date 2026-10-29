package org.xar.ck3.control.contracts.offline;

import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;

/** Shared deterministic per-Game journal layout; path derivation grants no runtime observation or writer authority. */
public final class IncidentJournalLayout {
    private IncidentJournalLayout() { }
    public record Scope(Path incidentRoot, Path scanRoot) {
        public Scope { canonical(incidentRoot); canonical(scanRoot); distinct(incidentRoot, scanRoot); }
    }
    public static Scope scope(Path incidentBase, Path scanBase, String machineId, GameGeneration game,
            String sessionId, String episodeId, ExactRef sourceRef) {
        canonical(incidentBase); canonical(scanBase); distinct(incidentBase, scanBase);
        StrictJson.require(machineId != null && !machineId.equals("unknown") && machineId.matches("[a-z0-9][a-z0-9-]{0,63}"), "Explicit actual journal machine required");
        Objects.requireNonNull(game); Objects.requireNonNull(sourceRef); bounded(sessionId); bounded(episodeId);
        canonical(Path.of(sourceRef.path()));
        var identity = StrictJson.object().put("machine_id", machineId).put("session_id", sessionId).put("episode_run_id", episodeId);
        identity.set("game", game.toJson()); identity.set("source_ref", sourceRef.toJson());
        final String key;
        try { key = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(StrictJson.canonical(identity))); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
        return new Scope(incidentBase.resolve(key), scanBase.resolve(key));
    }
    private static void bounded(String value) { StrictJson.text(value); StrictJson.require(value.length() <= 4096, "Bounded actual journal identity required"); }
    private static void canonical(Path value) {
        Objects.requireNonNull(value); String text = value.toString();
        StrictJson.require(value.isAbsolute() && value.equals(value.normalize()) && text.length() <= 4096
                && text.chars().noneMatch(c -> c < 32 || c == 127), "Canonical absolute journal role root required");
    }
    private static void distinct(Path first, Path second) { StrictJson.require(!first.startsWith(second) && !second.startsWith(first), "Separate fixed incident and scan bases required"); }
}
