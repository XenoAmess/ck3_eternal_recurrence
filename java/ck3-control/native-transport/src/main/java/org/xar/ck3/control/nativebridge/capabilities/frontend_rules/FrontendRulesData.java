package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** Domain values from the actual native frontend model. No map/player identity is invented. */
public final class FrontendRulesData {
    private FrontendRulesData() { }
    public static final BigInteger U64_MAX = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    public enum Build {
        CK3_11906("1.19.0.6", "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"),
        CK3_12002("1.20.0.2", "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"),
        CK3_12003("1.20.0.3", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"),
        CK3_12004("1.20.0.4", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
        private final String version;
        private final String sha256;
        Build(String version, String sha256) { this.version = version; this.sha256 = sha256; }
        public String version() { return version; }
        public String sha256() { return sha256; }
        public String adapterId() { return "ck3-" + version + "-msvc-x64"; }
        public String backendId(String suffix) { return "ck3-" + version + "-native-" + suffix; }
        public static Build require(String version, String sha256) {
            for (Build value : values()) if (value.version.equals(version) && value.sha256.equalsIgnoreCase(sha256)) return value;
            throw new IllegalArgumentException("mixed or unknown exact native build");
        }
        public void requireRules() { FrontendRulesData.require(this == CK3_12003 || this == CK3_12004, "rules require actual .3/.4"); }
        public void requireFrontend() { FrontendRulesData.require(this != CK3_12002, "frontend route build is not admitted"); }
    }
    public record Binding(long bridgePid, BigInteger connectionGeneration) {
        public Binding { require(bridgePid >= 1 && bridgePid <= 0xffff_ffffL, "positive u32 bridge PID required"); positiveU64(connectionGeneration); }
    }
    public record Source(Binding binding, Build build) {
        public Source { Objects.requireNonNull(binding); Objects.requireNonNull(build); build.requireFrontend(); }
    }
    public enum Route {
        UNAVAILABLE("unavailable"), MAIN_MENU("main_menu"), BOOKMARKS("bookmarks"), LOBBY("lobby"),
        RULER_DESIGNER("ruler_designer"), COAT_OF_ARMS_DESIGNER("coat_of_arms_designer");
        private final String wire;
        Route(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Route require(String value) {
            for (Route route : values()) if (route.wire.equals(value)) return route;
            throw new IllegalArgumentException("unknown native frontend route");
        }
    }
    public record ObservedRoute(Route route, Source source, BigInteger querySequence) {
        public ObservedRoute { Objects.requireNonNull(route); Objects.requireNonNull(source); positiveU64(querySequence); }
    }
    public record ScriptKey(String value) {
        public ScriptKey { require(value != null && value.matches("[A-Za-z0-9_]{1,96}"), "actual script key required"); }
    }
    public record Selection(ScriptKey ruleKey, ScriptKey selectedSettingKey) {
        public Selection { Objects.requireNonNull(ruleKey); Objects.requireNonNull(selectedSettingKey); }
    }
    public record RuleSelections(Source source, BigInteger querySequence, boolean ready, String unavailableReason,
            List<Selection> selections, boolean appliedSettingsProven) {
        public RuleSelections {
            Objects.requireNonNull(source); source.build().requireRules(); positiveU64(querySequence);
            Objects.requireNonNull(unavailableReason); selections = List.copyOf(selections);
            require(selections.size() <= 4096 && (ready ? !selections.isEmpty() && unavailableReason.isEmpty() : selections.isEmpty() && !unavailableReason.isEmpty()), "inconsistent rule readiness/vector");
            String previous = null;
            for (Selection row : selections) {
                String key = row.ruleKey().value(); require(previous == null || previous.compareTo(key) < 0, "rule IDs must be unique and sorted"); previous = key;
            }
        }
        public Optional<ScriptKey> selected(ScriptKey key) {
            return selections.stream().filter(row -> row.ruleKey().equals(key)).map(Selection::selectedSettingKey).findFirst();
        }
    }
    public record RuleWindow(Source source, BigInteger querySequence, boolean ready, String unavailableReason,
            boolean visible, boolean enabled, boolean host, boolean gameStarted, boolean mayEdit, boolean closed) {
        public RuleWindow {
            Objects.requireNonNull(source); source.build().requireRules(); positiveU64(querySequence); Objects.requireNonNull(unavailableReason);
            require(ready == unavailableReason.isEmpty(), "window availability contradicts reason");
            require(ready || !(visible || enabled || host || gameStarted || mayEdit || closed), "unavailable window invented state");
            require(mayEdit == (ready && visible && enabled && host && !gameStarted), "stock may-edit predicate drift");
            require(closed == (ready && !visible), "window closure predicate drift");
        }
    }
    public enum RulesAction {
        SELECT("select"), APPLY_AND_HIDE("apply_and_hide"), HIDE("hide");
        private final String wire;
        RulesAction(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record RulesAck(RulesAction action, Build build, boolean ready, String unavailableReason,
            boolean nativeInvoked, boolean selectionVerified, boolean applyInvoked, boolean hideInvoked, int nativeNextCalls) {
        public RulesAck {
            Objects.requireNonNull(action); Objects.requireNonNull(build); build.requireRules(); Objects.requireNonNull(unavailableReason);
            require(ready == unavailableReason.isEmpty(), "ACK readiness contradicts reason");
            require(nativeNextCalls >= 0 && nativeNextCalls <= 511, "native Next bound exceeded");
            if (action == RulesAction.SELECT) {
                require(!applyInvoked && !hideInvoked && (nativeNextCalls > 0) == nativeInvoked, "selection ACK callback drift");
                require(!ready || selectionVerified, "selection ACK lacks target readback");
            } else {
                require(nativeNextCalls == 0 && !selectionVerified, "window ACK contains selection state");
                require(action != RulesAction.HIDE || !applyInvoked, "Hide ACK invoked Apply");
                require(!ready || nativeInvoked && hideInvoked && (action != RulesAction.APPLY_AND_HIDE || applyInvoked), "window ACK lacks stock callbacks");
            }
        }
    }
    public record Widget(String runtimeName, String childPath, int depth, int childCount, BigInteger vtableRva,
            boolean effectiveVisible, boolean enabled) {
        public Widget {
            Objects.requireNonNull(runtimeName); Objects.requireNonNull(childPath); Objects.requireNonNull(vtableRva);
            require(runtimeName.getBytes(java.nio.charset.StandardCharsets.UTF_8).length <= 127, "native widget name too long");
            require(childPath.length() <= 383 && (childPath.isEmpty() || childPath.matches("[0-9]+(?:/[0-9]+)*")), "invalid child path");
            require(depth >= 0 && depth <= 64 && depth == (childPath.isEmpty() ? 0 : childPath.split("/").length), "widget path/depth mismatch");
            require(childCount >= 0 && childCount <= 4096 && vtableRva.signum() >= 0 && vtableRva.compareTo(U64_MAX) <= 0, "invalid widget native counts");
        }
    }
    public record GuiTree(Source source, BigInteger querySequence, String scopeRootName, boolean rootAvailable,
            boolean truncated, List<Widget> widgets) {
        public GuiTree {
            Objects.requireNonNull(source); positiveU64(querySequence); Objects.requireNonNull(scopeRootName); widgets = List.copyOf(widgets);
            require(List.of("", "_root_", "mainmenu_panel_bottom", "frontend_bookmarks", "game_rules", "lobbyview", "ruler_designer", "coat_of_arms_page", "coat_of_arms_pattern_grid").contains(scopeRootName), "unknown native GUI root");
            require(widgets.size() <= 2048, "frontend widget census limit exceeded");
        }
        public boolean visibleTarget(String scope, String path, String name) {
            return rootAvailable && scopeRootName.equals(scope) && widgets.stream().anyMatch(row -> row.childPath().equals(path) && row.runtimeName().equals(name) && row.effectiveVisible() && row.enabled());
        }
        public boolean defaultDesignerReady() { return visibleTarget("lobbyview", "3/0/2/3", ""); }
        public boolean randomPlayableReady() { return visibleTarget("lobbyview", "4/0/1/0/1", ""); }
    }
    public record BookmarkModel(Source source, BigInteger querySequence, boolean accepted, String status,
            boolean candidateIdentityReady, Optional<String> selectedBookmarkGroupKey, Optional<String> selectedBookmarkKey,
            BigInteger selectedDateRaw, int selectedDateLowRaw, List<String> candidateKeys, int targetIndex,
            int selectedIndex, Optional<String> governmentKey, boolean feudal, boolean dateMatches) {
        public BookmarkModel {
            Objects.requireNonNull(source); positiveU64(querySequence); Objects.requireNonNull(status); Objects.requireNonNull(selectedBookmarkGroupKey);
            Objects.requireNonNull(selectedBookmarkKey); Objects.requireNonNull(selectedDateRaw); candidateKeys = List.copyOf(candidateKeys); Objects.requireNonNull(governmentKey);
            require(candidateKeys.size() <= 4096 && selectedIndex >= -1 && selectedIndex < candidateKeys.size(), "native selected model index invalid");
        }
        /** Actual bookmark/date readback; this does not prove a selected character or gameplay actor. */
        public boolean supported1066BookmarkSelected() {
            return accepted && selectedBookmarkKey.equals(Optional.of("bm_1066_rags_to_riches"))
                    && selectedBookmarkGroupKey.equals(Optional.of("bm_group_1066")) && selectedDateLowRaw == 53144328;
        }
        public void requireSupported1066Bookmark() {
            require(supported1066BookmarkSelected(), "independent native model does not prove the 1066 bookmark/group/date");
        }
        public Candidate selected(String expectedKey, boolean scenario, boolean requireSelected) {
            require(scenario ? expectedKey.equals("bookmark_xar_faith_h01_abbasid")
                    : List.of("bookmark_rags_to_riches_petty_king_murchad", "bookmark_rags_to_riches_duke_robert").contains(expectedKey), "bookmark character outside exact allowlist");
            String bookmark = scenario ? "bm_xar_faith_h01_867" : "bm_1066_rags_to_riches";
            String group = scenario ? "bm_group_867" : "bm_group_1066";
            String government = scenario ? "clan_government" : "feudal_government";
            require(accepted && status.equals("identity_ready") && candidateIdentityReady && targetIndex >= 0 && targetIndex < candidateKeys.size(), "native bookmark identity unavailable");
            require(selectedBookmarkKey.equals(Optional.of(bookmark)) && (selectedBookmarkGroupKey.isEmpty() || selectedBookmarkGroupKey.get().equals(group)), "bookmark/group drift");
            require(candidateKeys.get(targetIndex).equals(expectedKey) && (!requireSelected || selectedIndex == targetIndex) && governmentKey.equals(Optional.of(government)) && dateMatches && (scenario ? selectedDateLowRaw == 51394920 : selectedDateLowRaw > 0 && feudal), "selected native candidate does not prove requested target");
            return new Candidate(source, querySequence, selectedBookmarkGroupKey, bookmark, expectedKey, government, selectedDateLowRaw, scenario);
        }
    }
    public record Candidate(Source source, BigInteger querySequence, Optional<String> bookmarkGroupKey, String bookmarkKey,
            String characterNameKey, String governmentKey, int dateRaw, boolean scenario) {
        public Candidate { Objects.requireNonNull(source); positiveU64(querySequence); Objects.requireNonNull(bookmarkGroupKey); Objects.requireNonNull(bookmarkKey); Objects.requireNonNull(characterNameKey); Objects.requireNonNull(governmentKey); }
    }
    public record NativeAck(String step, String backendId, String status) {
        public NativeAck { require(step != null && !step.isEmpty(), "ACK step required"); require("native-headless".equals(backendId), "ACK backend drift"); require("acknowledged_verification_pending".equals(status), "ACK must retain verification pending"); }
    }
    public static void positiveU64(BigInteger value) { require(value != null && value.signum() > 0 && value.compareTo(U64_MAX) <= 0, "positive uint64 required"); }
    public static void require(boolean condition, String message) { if (!condition) throw new IllegalArgumentException(message); }
}
