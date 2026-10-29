package org.xar.ck3.control.platform;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import java.util.HashSet;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.SteamOfflineObservation.Common;
import org.xar.ck3.control.platform.SteamOfflineObservation.Endpoint;
import org.xar.ck3.control.platform.SteamOfflineObservation.Method;
import org.xar.ck3.control.platform.SteamOfflineObservation.NativeEvidence;
import org.xar.ck3.control.platform.SteamOfflineObservation.Offline;
import org.xar.ck3.control.platform.SteamOfflineObservation.Online;
import org.xar.ck3.control.platform.SteamOfflineObservation.Reason;
import org.xar.ck3.control.platform.SteamOfflineObservation.Result;
import org.xar.ck3.control.platform.SteamOfflineObservation.Source;
import org.xar.ck3.control.platform.SteamOfflineObservation.SteamProcess;
import org.xar.ck3.control.platform.SteamOfflineObservation.Unavailable;

/** Exact original v2 wire for both producers; explicit v1 archive migration never mints admission. */
public final class SteamOfflineObservationCodec {
    public static final String SCHEMA = "xar.steam-offline-state-probe/v2";
    public static final int MAXIMUM_BYTES = 1048576;
    private static final Set<String> COMMON = Set.of("schema", "machine_id", "observed_at_utc", "nonce", "status",
            "reason", "steam", "source", "endpoint", "diagnostics");
    private SteamOfflineObservationCodec() { }
    public static byte[] encode(Result value) { return StrictJson.canonical(toJson(value), MAXIMUM_BYTES); }
    public static Result decode(byte[] bytes) { return fromJson(StrictJson.parse(bytes, MAXIMUM_BYTES)); }
    public static ObjectNode toJson(Result value) {
        Common data = value.common(); ObjectNode root = StrictJson.object();
        root.put("schema", SCHEMA); root.put("machine_id", data.machineId()); root.put("observed_at_utc", data.observedAtUtc());
        root.put("nonce", data.nonce()); root.put("status", value.status().name().toLowerCase(Locale.ROOT));
        Reason reason = value instanceof Unavailable missing ? missing.reason() : Reason.OBSERVED;
        root.put("reason", reason.name().toLowerCase(Locale.ROOT));
        root.set("steam", data.steam().map(SteamOfflineObservationCodec::process).orElse(null));
        root.set("source", data.source().map(SteamOfflineObservationCodec::source).orElse(null));
        root.set("endpoint", data.endpoint().map(SteamOfflineObservationCodec::endpoint).orElse(null));
        ArrayNode diagnostics = root.putArray("diagnostics"); data.diagnostics().forEach(diagnostics::add);
        if (value instanceof Offline offline) {
            root.put("offline_mode", true); root.put("observation_method", method(offline.method()));
            root.set("native_evidence", offline.nativeEvidence().map(SteamOfflineObservationCodec::nativeEvidence).orElse(null));
        } else if (value instanceof Online) {
            root.put("offline_mode", false); root.put("observation_method", "cef_app_getters"); root.putNull("native_evidence");
        } else { root.putNull("observation_method"); root.putNull("native_evidence"); }
        return root;
    }
    public static Result fromJson(JsonNode node) {
        String schema = text(node, "schema"), status = text(node, "status");
        boolean current = schema.equals(SCHEMA);
        StrictJson.require(current || schema.equals("xar.steam-offline-state-probe/v1"), "Known Steam receipt schema required");
        StrictJson.require(Set.of("offline", "online", "unavailable").contains(status), "Known Steam status required");
        Set<String> fields = new HashSet<>(COMMON);
        if (current) { fields.add("observation_method"); fields.add("native_evidence"); }
        if (!status.equals("unavailable")) fields.add("offline_mode");
        ObjectNode root = StrictJson.object(node, fields);
        Common common = new Common(text(root, "machine_id"), text(root, "observed_at_utc"), text(root, "nonce"),
                optionalProcess(root.get("steam")), optionalSource(root.get("source")), optionalEndpoint(root.get("endpoint")), strings(root.get("diagnostics")));
        Reason reason = Reason.valueOf(text(root, "reason").toUpperCase(Locale.ROOT));
        if (status.equals("unavailable")) {
            if (current) StrictJson.require(root.get("observation_method").isNull() && root.get("native_evidence").isNull(), "Unavailable has no verified provenance");
            return new Unavailable(common, reason);
        }
        StrictJson.require(reason == Reason.OBSERVED && root.get("offline_mode").isBoolean()
                && root.get("offline_mode").booleanValue() == status.equals("offline"), "Actual mode boolean and observed reason required");
        Method method = current ? parseMethod(text(root, "observation_method")) : Method.CEF_APP_GETTERS;
        Optional<NativeEvidence> evidence = !current || root.get("native_evidence").isNull()
                ? Optional.empty() : Optional.of(nativeEvidence(root.get("native_evidence")));
        if (status.equals("offline")) return new Offline(common, method, evidence);
        StrictJson.require(method == Method.CEF_APP_GETTERS && evidence.isEmpty(), "Native zero does not qualify online");
        return new Online(common);
    }
    private static String method(Method value) { return value.name().toLowerCase(Locale.ROOT); }
    private static Method parseMethod(String value) {
        return switch (value) { case "native_current_user_byte" -> Method.NATIVE_CURRENT_USER_BYTE;
            case "cef_app_getters" -> Method.CEF_APP_GETTERS; default -> throw new IllegalArgumentException("Unknown Steam observation method"); };
    }
    private static ObjectNode process(SteamProcess value) {
        ObjectNode node = StrictJson.object(); node.put("pid", value.pid()); node.put("birth_filetime", value.birthFiletime());
        node.put("exe", value.executable()); node.put("file_version", value.fileVersion()); return node;
    }
    private static SteamProcess process(JsonNode node) {
        StrictJson.object(node, Set.of("pid", "birth_filetime", "exe", "file_version"));
        return new SteamProcess(StrictJson.integer(node.get("pid"), 1, 0xffff_ffffL), text(node, "birth_filetime"), text(node, "exe"), text(node, "file_version"));
    }
    private static ObjectNode source(Source value) {
        ObjectNode node = StrictJson.object(); node.put("path", value.path()); node.put("bytes", value.bytes()); node.put("sha256", value.sha256());
        node.put("file_id", value.fileId()); node.put("mtime_ns", value.mtimeNanos()); return node;
    }
    private static Source source(JsonNode node) {
        StrictJson.object(node, Set.of("path", "bytes", "sha256", "file_id", "mtime_ns"));
        return new Source(text(node, "path"), StrictJson.integer(node.get("bytes"), 1, StrictJson.MAX_SAFE_INTEGER), text(node, "sha256"), text(node, "file_id"), text(node, "mtime_ns"));
    }
    private static ObjectNode endpoint(Endpoint value) {
        ObjectNode node = StrictJson.object(); node.put("pid", value.pid()); node.put("birth_filetime", value.birthFiletime());
        node.put("port", value.port()); node.put("target_id", value.targetId()); node.put("target_url", value.targetUrl()); return node;
    }
    private static Endpoint endpoint(JsonNode node) {
        StrictJson.object(node, Set.of("pid", "birth_filetime", "port", "target_id", "target_url"));
        return new Endpoint(StrictJson.integer(node.get("pid"), 1, 0xffff_ffffL), text(node, "birth_filetime"),
                (int) StrictJson.integer(node.get("port"), 1, 65535), text(node, "target_id"), text(node, "target_url"));
    }
    private static ObjectNode nativeEvidence(NativeEvidence value) {
        ObjectNode node = StrictJson.object(); node.put("machine_id", value.machineId()); node.put("observed_at_utc", value.observedAtUtc());
        node.put("nonce", value.nonce()); node.put("module_base", value.moduleBase()); node.put("module_size", value.moduleSize());
        node.put("value_rva", value.valueRva()); node.put("value_address", value.valueAddress()); node.put("producer_rva", value.producerRva());
        node.put("producer_anchor_hex", value.producerAnchorHex()); node.put("producer_anchor_sha256", value.producerAnchorSha256());
        ArrayNode raw = node.putArray("raw_samples"); value.rawSamples().forEach(raw::add);
        node.set("steam_before", process(value.steamBefore())); node.set("steam_after", process(value.steamAfter()));
        node.set("source_before", source(value.sourceBefore())); node.set("source_after", source(value.sourceAfter()));
        node.put("tray_manager_pointer_rva", value.trayManagerPointerRva()); node.put("tray_manager_address", value.trayManagerAddress());
        node.put("tray_state_offset", value.trayStateOffset()); ArrayNode tray = node.putArray("tray_state_samples"); value.trayStateSamples().forEach(tray::add); return node;
    }
    private static NativeEvidence nativeEvidence(JsonNode node) {
        StrictJson.object(node, Set.of("machine_id", "observed_at_utc", "nonce", "module_base", "module_size", "value_rva", "value_address",
                "producer_rva", "producer_anchor_hex", "producer_anchor_sha256", "raw_samples", "steam_before", "steam_after", "source_before",
                "source_after", "tray_manager_pointer_rva", "tray_manager_address", "tray_state_offset", "tray_state_samples"));
        return new NativeEvidence(text(node, "machine_id"), text(node, "observed_at_utc"), text(node, "nonce"), text(node, "module_base"),
                StrictJson.integer(node.get("module_size"), 1, 0xffff_ffffL), text(node, "value_rva"), text(node, "value_address"), text(node, "producer_rva"),
                text(node, "producer_anchor_hex"), text(node, "producer_anchor_sha256"), pair(node.get("raw_samples"), 0, 1),
                process(node.get("steam_before")), process(node.get("steam_after")), source(node.get("source_before")), source(node.get("source_after")),
                text(node, "tray_manager_pointer_rva"), text(node, "tray_manager_address"), text(node, "tray_state_offset"), pair(node.get("tray_state_samples"), 4, 4));
    }
    private static List<Integer> pair(JsonNode node, int minimum, int maximum) {
        StrictJson.require(node != null && node.isArray() && node.size() == 2, "Two actual integer samples required");
        return List.of((int) StrictJson.integer(node.get(0), minimum, maximum), (int) StrictJson.integer(node.get(1), minimum, maximum));
    }
    private static List<String> strings(JsonNode node) {
        StrictJson.require(node != null && node.isArray() && node.size() <= 256, "Bounded diagnostics array required");
        List<String> result = new ArrayList<>(); for (JsonNode value : node) result.add(StrictJson.text(value)); return List.copyOf(result);
    }
    private static Optional<SteamProcess> optionalProcess(JsonNode node) { return node.isNull() ? Optional.empty() : Optional.of(process(node)); }
    private static Optional<Source> optionalSource(JsonNode node) { return node.isNull() ? Optional.empty() : Optional.of(source(node)); }
    private static Optional<Endpoint> optionalEndpoint(JsonNode node) { return node.isNull() ? Optional.empty() : Optional.of(endpoint(node)); }
    private static String text(JsonNode node, String field) { StrictJson.require(node != null && node.isObject(), "Steam object required"); return StrictJson.text(node.get(field)); }
}
