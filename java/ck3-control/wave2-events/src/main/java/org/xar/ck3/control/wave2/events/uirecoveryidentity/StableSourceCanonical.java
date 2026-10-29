package org.xar.ck3.control.wave2.events.uirecoveryidentity;

import static org.xar.ck3.control.wave2.events.uirecoveryidentity.UiRecoverySourceModel.*;

import java.util.List;
import java.util.Optional;

/** Exact Python ensure_ascii=False/sort_keys/separators JSON for this closed stable-source type. */
final class StableSourceCanonical {
    private StableSourceCanonical() { }
    static String source(StableSource source) {
        return "{\"backend_sha256\":" + quote(source.backendSha256()) + ",\"choice_catalogue\":" + choices(source.catalogue())
                + ",\"game_exe_sha256\":" + quote(source.gameExeSha256()) + ",\"native_adapter_id\":" + quote(source.nativeAdapterId())
                + ",\"root_runtime_name\":" + quote(source.rootRuntimeName()) + ",\"root_type\":" + quote(source.rootType())
                + ",\"root_vtable_module_rva\":" + address(source.rootVtable()) + "}";
    }
    static String choice(NormalizedChoice choice) {
        return "{\"callback_identities\":" + callbacks(choice.callbacks()) + ",\"label\":" + nullable(choice.label())
                + ",\"role\":" + nullable(choice.role()) + ",\"runtime_name\":" + quote(choice.runtimeName())
                + ",\"widget_vtable_module_rva\":" + address(choice.widgetVtable()) + "}";
    }
    static String callback(Callback callback) {
        return "{\"function_module_rva\":" + address(callback.function()) + ",\"vtable_module_rva\":" + address(callback.vtable()) + "}";
    }
    private static String callbacks(List<Callback> callbacks) { return "[" + String.join(",", callbacks.stream().map(StableSourceCanonical::callback).toList()) + "]"; }
    private static String choices(List<NormalizedChoice> choices) { return "[" + String.join(",", choices.stream().map(StableSourceCanonical::choice).toList()) + "]"; }
    private static String address(RelativeAddress address) {
        return address instanceof NumericAddress value ? value.value().toString() : quote(((SymbolicAddress) address).value());
    }
    private static String nullable(Optional<String> value) { return value.map(StableSourceCanonical::quote).orElse("null"); }
    private static String quote(String value) {
        StringBuilder result = new StringBuilder("\""); String hexadecimal = "0123456789abcdef";
        for (int index = 0; index < value.length(); index++) {
            char current = value.charAt(index);
            switch (current) {
                case '"' -> result.append("\\\""); case '\\' -> result.append("\\\\");
                case '\b' -> result.append("\\b"); case '\f' -> result.append("\\f");
                case '\n' -> result.append("\\n"); case '\r' -> result.append("\\r"); case '\t' -> result.append("\\t");
                default -> {
                    if (current < 0x20) { result.append("\\u00").append(hexadecimal.charAt(current >> 4)).append(hexadecimal.charAt(current & 15)); }
                    else { result.append(current); }
                }
            }
        }
        return result.append('"').toString();
    }
    static int compareUnicode(String left, String right) {
        int a = 0; int b = 0;
        while (a < left.length() && b < right.length()) {
            int x = left.codePointAt(a); int y = right.codePointAt(b);
            if (x != y) { return Integer.compare(x, y); }
            a += Character.charCount(x); b += Character.charCount(y);
        }
        return Integer.compare(left.length() - a, right.length() - b);
    }
}
