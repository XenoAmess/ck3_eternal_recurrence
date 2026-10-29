package org.xar.ck3.control.wave2.events.registered;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.registered.RegistryJson.*;

/** Source-pinned policy-input projection of the original public knowledge producer.
 * This is neither a recommendation cache nor a live Game/source authorization.
 * It retains all contracts, consumed analysis fields, and complete source indexes.
 */
public final class RegisteredEventKnowledge {
    public static final String RESOURCE = "/org/xar/ck3/control/events/registered-policy-inputs-v1.json.gz";
    public static final String INPUT_SHA256 = "446b4ba71c228820fe95c6faa6351ac1e5da0aeb599dd568c3939a904c0f4b07";
    public static final String EXPANDED_SHA256 = "3fd420e33bf7728591608bec8e436eb7c14b38df44dbbd176ec36217238efd22";
    public static final Map<String,String> EXE = Map.of(
        "1.19.0.6", "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
        "1.20.0.2", "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
        "1.20.0.3", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6",
        "1.20.0.4", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
    private final ObjectValue document;
    private final java.util.concurrent.ConcurrentMap<String,EventSourceIndex.Index> sourceIndexes=new java.util.concurrent.ConcurrentHashMap<>();
    private RegisteredEventKnowledge(ObjectValue document) { this.document = document; }
    public static RegisteredEventKnowledge load() throws IOException {
        try (InputStream input = RegisteredEventKnowledge.class.getResourceAsStream(RESOURCE)) {
            if (input == null) throw new IOException("registered policy input resource absent");
            return decode(input.readNBytes(216_014));
        }
    }
    /** Byte limit and both source hashes are checked before constructing usable knowledge. */
    public static RegisteredEventKnowledge decode(byte[] compressed) throws IOException {
        Objects.requireNonNull(compressed);
        StrictJson.require(compressed.length == 216_013 && sha(compressed).equals(INPUT_SHA256), "registered knowledge source bytes drift");
        byte[] expanded;
        try (GZIPInputStream gzip = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
            expanded = gzip.readNBytes(2_239_613);
            StrictJson.require(expanded.length == 2_239_612 && gzip.read() == -1, "bounded complete registered knowledge required");
        }
        StrictJson.require(sha(expanded).equals(EXPANDED_SHA256), "registered knowledge expanded bytes drift");
        ObjectValue document = RetainedJson.object(RetainedJson.parse(expanded, new RetainedJson.ParseBudget(2_239_612, 500_000, 96)));
        StrictJson.require(document.fields().keySet().equals(EXE.keySet()), "exact supported registered builds required");
        for (String build : EXE.keySet()) {
            ObjectValue table = obj(get(document,build)); ObjectValue rows = obj(get(table,"knowledge"));
            StrictJson.require(rows.fields().size() == (build.equals("1.20.0.4") ? 198 : 195), "complete original registered key union required");
            ObjectValue index = obj(get(table,"source_index"));
            StrictJson.require(is(get(index,"ck3_build"),build) && is(get(index,"ck3_exe_sha256"),EXE.get(build)) && object(get(index,"events")), "exact indexed build/source identity required");
            for (var row : rows.fields().entrySet()) {
                Value value = row.getValue();
                StrictJson.require(object(value) && is(get(value,"ck3_build"),build) && is(get(value,"ck3_exe_sha256"),EXE.get(build))
                    && is(get(value,"event_definition_key"),row.getKey()) && Set.of("available","unavailable").contains(str(get(value,"status"))), "registered knowledge row identity drift");
                if (is(get(value,"status"),"available")) StrictJson.require(object(get(value,"contract")), "available contract required");
            }
        }
        return new RegisteredEventKnowledge(document);
    }
    public Set<String> keys(String build) { return names(get(get(document,build),"knowledge")); }
    public ObjectValue query(String build, String key) {
        Objects.requireNonNull(build); Objects.requireNonNull(key);
        Value row = get(get(get(document,build),"knowledge"),key);
        if (row instanceof ObjectValue object) return object;
        return b().set("status","unavailable").set("ck3_build",build).set("ck3_exe_sha256",EXE.get(build))
            .set("event_definition_key",key).set("contract",RetainedJson.NULL).set("analysis",RetainedJson.NULL)
            .set("unavailable_reason",EXE.containsKey(build) ? "event_definition_key_not_registered" : "unsupported_ck3_build").build();
    }
    /** Complete lexical source row. Caller candidates remain lexical, never promoted to call authority. */
    public ObjectValue indexed(String build, String key) { return obj(get(get(get(get(document,build),"source_index"),"events"),key)); }
    /** Same frozen complete source index, validated once before exposing shared typed rows. */
    public EventSourceIndex.Index sourceIndex(String build) {
        StrictJson.require(EXE.containsKey(Objects.requireNonNull(build)),"unsupported source-index build");
        return sourceIndexes.computeIfAbsent(build,key->EventSourceIndex.decode(obj(get(get(document,key),"source_index"))));
    }
    public String sourceDatasetSha256(String build) { return text(get(get(get(document,build),"source_index"),"dataset_sha256")); }
    public static String contextBuild(ObjectValue context) {
        String build = text(context.get("ck3_build")); if (build != null) return build;
        Value provenance = context.get("provenance"); build = text(get(provenance,"ck3_build")); if (build != null) return build;
        for (String candidate : List.of("1.19.0.6","1.20.0.2","1.20.0.3","1.20.0.4"))
            if (is(get(provenance,"backend_id"),"ck3-" + candidate + "-native-event-window-v1")) return candidate;
        return "1.19.0.6";
    }
    public static boolean migrated(String build) { return Set.of("1.20.0.2","1.20.0.3","1.20.0.4").contains(build); }
    private static String sha(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException impossible) { throw new AssertionError(impossible); }
    }
}
