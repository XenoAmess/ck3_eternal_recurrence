package com.xenoamess.ck3coa;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.equalTo;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import io.quarkus.test.InjectMock;
import io.quarkus.test.junit.QuarkusTest;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

@QuarkusTest
class CoatOfArmsResourceTest {
    @InjectMock
    CoatOfArmsMcpClient mcp;

    private static Map<String, Object> nativeCapabilities(
            boolean snapshot,
            boolean connected) {
        List<String> capabilities = List.of(
                "game.command.probe-coat-of-arms-source-v1",
                "game.command.export-coat-of-arms-source-v1");
        return Map.of(
                "backend_id", "native-headless",
                "mode", "native-headless",
                "source", "injected-dll-named-pipe",
                "visual_fallback", false,
                "snapshot", snapshot,
                "bridge_capabilities", capabilities,
                "diagnostics", Map.of(
                        "connected", connected,
                        "connection_generation", 3,
                        "bridge_pid", 19424,
                        "hello", Map.of(
                                "ck3_build_match", true,
                                "game_adapter_status", "ready",
                                "expected_ck3_version", "1.19.0.6",
                                "expected_ck3_sha256",
                                "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
                                "connection_generation", 3,
                                "pid", 19424,
                                "capabilities", capabilities)));
    }

    @Test
    void sessionExposesTheCurrentMcpRevision() {
        when(mcp.callTool(eq("ck3_take_snapshot"), eq(Map.of())))
                .thenReturn(Map.of("revision", 7, "source", "native"));

        given()
                .when().get("/api/ck3/coat-of-arms/session")
                .then()
                .statusCode(200)
                .body("revision", equalTo(7))
                .body("source", equalTo("native"));
    }

    @Test
    void sourceBindingUsesRevisionZeroForAnExactConnectedFrontend() {
        when(mcp.callTool(eq("ck3_get_capabilities"), eq(Map.of())))
                .thenReturn(nativeCapabilities(false, true));

        given()
                .when().get("/api/ck3/coat-of-arms/binding")
                .then()
                .statusCode(200)
                .body("schema", equalTo("coat-of-arms-source-binding-v1"))
                .body("status", equalTo("bound"))
                .body("revision_source", equalTo("frontend"))
                .body("revision", equalTo(0))
                .body("connection_generation", equalTo(3))
                .body("bridge_pid", equalTo(19424));

        verify(mcp).callTool("ck3_get_capabilities", Map.of());
    }

    @Test
    void sourceBindingUsesThePositiveSnapshotRevisionWhenAvailable() {
        when(mcp.callTool(eq("ck3_get_capabilities"), eq(Map.of())))
                .thenReturn(nativeCapabilities(true, true));
        when(mcp.callTool(eq("ck3_take_snapshot"), eq(Map.of())))
                .thenReturn(Map.of("revision", 17, "source", "native"));

        given()
                .when().get("/api/ck3/coat-of-arms/binding")
                .then()
                .statusCode(200)
                .body("status", equalTo("bound"))
                .body("revision_source", equalTo("snapshot"))
                .body("revision", equalTo(17));

        verify(mcp).callTool("ck3_take_snapshot", Map.of());
    }

    @Test
    void sourceBindingRejectsADisconnectedFrontend() {
        when(mcp.callTool(eq("ck3_get_capabilities"), eq(Map.of())))
                .thenReturn(nativeCapabilities(false, false));

        given()
                .when().get("/api/ck3/coat-of-arms/binding")
                .then()
                .statusCode(503)
                .body("status", equalTo("mcp_unavailable"));
    }

    @Test
    void nativeDesignerActionIsAClosedZeroInputMcpCall() {
        when(mcp.callTool(
                        eq("ck3_activate_frontend_coat_of_arms_designer_v1"),
                        eq(Map.of())))
                .thenReturn(Map.of(
                        "status", "verified",
                        "action", "open_coat_of_arms_designer"));

        given()
                .contentType("application/json")
                .body(Map.of())
                .when().post("/api/ck3/coat-of-arms/open-native-designer")
                .then()
                .statusCode(200)
                .body("status", equalTo("verified"))
                .body("action", equalTo("open_coat_of_arms_designer"));

        verify(mcp).callTool(
                "ck3_activate_frontend_coat_of_arms_designer_v1", Map.of());
    }

    @Test
    void nativeDynastyCommitIsAClosedZeroInputMcpCall() {
        when(mcp.callTool(
                        eq("ck3_commit_frontend_dynasty_coat_of_arms_v1"),
                        eq(Map.of())))
                .thenReturn(Map.of(
                        "status", "verified",
                        "action", "commit_dynasty_coat_of_arms"));

        given()
                .contentType("application/json")
                .body(Map.of())
                .when().post("/api/ck3/coat-of-arms/commit-native-design")
                .then()
                .statusCode(200)
                .body("status", equalTo("verified"))
                .body("action", equalTo("commit_dynasty_coat_of_arms"));

        verify(mcp).callTool(
                "ck3_commit_frontend_dynasty_coat_of_arms_v1", Map.of());
    }

    @Test
    void nativeDesignerTreeIsAScopedZeroInputMcpCall() {
        when(mcp.callTool(
                        eq("ck3_inspect_frontend_coat_of_arms_tree_v1"),
                        eq(Map.of())))
                .thenReturn(Map.of(
                        "status", "available",
                        "scope_root_name", "coat_of_arms_page"));

        given()
                .when().get("/api/ck3/coat-of-arms/native-designer-tree")
                .then()
                .statusCode(200)
                .body("status", equalTo("available"))
                .body("scope_root_name", equalTo("coat_of_arms_page"));

        verify(mcp).callTool(
                "ck3_inspect_frontend_coat_of_arms_tree_v1", Map.of());
    }

    @Test
    void nativeCustomModeIsAClosedZeroInputMcpCall() {
        when(mcp.callTool(
                        eq("ck3_activate_frontend_coat_of_arms_custom_mode_v1"),
                        eq(Map.of())))
                .thenReturn(Map.of(
                        "status", "verified",
                        "action", "enter_coat_of_arms_custom_mode"));

        given()
                .contentType("application/json")
                .body(Map.of())
                .when().post("/api/ck3/coat-of-arms/enter-native-custom-mode")
                .then()
                .statusCode(200)
                .body("status", equalTo("verified"))
                .body("action", equalTo("enter_coat_of_arms_custom_mode"));

        verify(mcp).callTool(
                "ck3_activate_frontend_coat_of_arms_custom_mode_v1", Map.of());
    }

    @Test
    void resourceCatalogIsForwardedToTheMcpTool() {
        Map<String, Object> response = Map.of(
                "schema", "ck3-coat-of-arms-resource-catalog-v1",
                "total", 42);
        when(mcp.callTool(
                        eq("ck3_query_coat_of_arms_resource_catalog_v1"),
                        eq(Map.of(
                                "game_directory", "fixture-game",
                                "kind", "pattern",
                                "query", "solid",
                                "visible_only", true,
                                "offset", 0,
                                "limit", 25))))
                .thenReturn(response);

        given()
                .queryParam("kind", "pattern")
                .queryParam("query", "solid")
                .queryParam("limit", 25)
                .when().get("/api/ck3/coat-of-arms/resources")
                .then()
                .statusCode(200)
                .body("schema", equalTo("ck3-coat-of-arms-resource-catalog-v1"))
                .body("total", equalTo(42));
    }

    @Test
    void resourceAssetIsReadThroughTheMcpTool() {
        when(mcp.callTool(
                        eq("ck3_read_coat_of_arms_resource_asset_v1"),
                        eq(Map.of(
                                "game_directory", "fixture-game",
                                "kind", "pattern",
                                "name", "pattern_alpha.dds"))))
                .thenReturn(Map.of(
                        "schema", "ck3-coat-of-arms-resource-asset-v1",
                        "asset_base64", "RERTIA=="));

        given()
                .queryParam("kind", "pattern")
                .queryParam("name", "pattern_alpha.dds")
                .when().get("/api/ck3/coat-of-arms/asset")
                .then()
                .statusCode(200)
                .body("schema", equalTo("ck3-coat-of-arms-resource-asset-v1"))
                .body("asset_base64", equalTo("RERTIA=="));
    }

    @Test
    void renderSupportIsReadThroughTheMcpTool() {
        when(mcp.callTool(
                        eq("ck3_read_coat_of_arms_render_support_v1"),
                        eq(Map.of("game_directory", "fixture-game"))))
                .thenReturn(Map.of(
                        "schema", "ck3-coat-of-arms-render-support-v1",
                        "ck3_build", "1.19.0.6"));

        given()
                .when().get("/api/ck3/coat-of-arms/render-support")
                .then()
                .statusCode(200)
                .body("schema", equalTo("ck3-coat-of-arms-render-support-v1"))
                .body("ck3_build", equalTo("1.19.0.6"));
    }

    @Test
    void loadConfigurationIsReadThroughTheMcpTool() {
        when(mcp.callTool(
                        eq("ck3_query_coat_of_arms_load_configuration_v1"),
                        eq(Map.of("user_directory", "fixture-user"))))
                .thenReturn(Map.of(
                        "schema", "ck3-coat-of-arms-load-configuration-v1",
                        "enabled_mod_count", 2));

        given()
                .when().get("/api/ck3/coat-of-arms/load-configuration")
                .then()
                .statusCode(200)
                .body("schema", equalTo(
                        "ck3-coat-of-arms-load-configuration-v1"))
                .body("enabled_mod_count", equalTo(2));
    }

    @Test
    void installedDlcSourcesKeepTheirStaticProvenance() {
        when(mcp.callTool(
                        eq("ck3_query_coat_of_arms_installed_dlc_sources_v1"),
                        eq(Map.of("game_directory", "fixture-game"))))
                .thenReturn(Map.of(
                        "schema", "ck3-coat-of-arms-installed-dlc-sources-v1",
                        "installed_descriptor_count", 29,
                        "dlc_with_coa_candidates", 0));

        given()
                .when().get("/api/ck3/coat-of-arms/dlc-sources")
                .then()
                .statusCode(200)
                .body("schema", equalTo(
                        "ck3-coat-of-arms-installed-dlc-sources-v1"))
                .body("installed_descriptor_count", equalTo(29))
                .body("dlc_with_coa_candidates", equalTo(0));
    }

    @Test
    void runtimeFeaturesUseTheBoundSnapshotRevision() {
        when(mcp.callTool(
                        eq("ck3_query_loaded_feature_manifest_v1"),
                        eq(Map.of("expected_revision", 7L))))
                .thenReturn(Map.of(
                        "schema", "loaded-feature-manifest-v1",
                        "status", "available",
                        "snapshot_revision", 31));

        given()
                .queryParam("expectedRevision", 7)
                .when().get("/api/ck3/coat-of-arms/runtime-features")
                .then()
                .statusCode(200)
                .body("schema", equalTo("loaded-feature-manifest-v1"))
                .body("status", equalTo("available"))
                .body("snapshot_revision", equalTo(31));

        given()
                .when().get("/api/ck3/coat-of-arms/runtime-features")
                .then()
                .statusCode(400);
    }

    @Test
    void configuredCatalogPreservesFiltersAndCandidateProvenance() {
        when(mcp.callTool(
                        eq("ck3_query_coat_of_arms_configured_resource_catalog_v1"),
                        eq(Map.of(
                                "user_directory", "fixture-user",
                                "kind", "pattern",
                                "query", "lion",
                                "visible_only", true,
                                "offset", 0,
                                "limit", 25))))
                .thenReturn(Map.of(
                        "schema",
                        "ck3-coat-of-arms-configured-resource-catalog-v1",
                        "total",
                        2));

        given()
                .queryParam("kind", "pattern")
                .queryParam("query", "lion")
                .queryParam("limit", 25)
                .when().get("/api/ck3/coat-of-arms/configured-resources")
                .then()
                .statusCode(200)
                .body("schema", equalTo(
                        "ck3-coat-of-arms-configured-resource-catalog-v1"))
                .body("total", equalTo(2));
    }

    @Test
    void configuredAssetUsesOpaqueCandidateIdentity() {
        String candidateId = "A".repeat(64);
        when(mcp.callTool(
                        eq("ck3_read_coat_of_arms_configured_resource_asset_v1"),
                        eq(Map.of(
                                "user_directory", "fixture-user",
                                "kind", "colored_emblem",
                                "candidate_id", candidateId))))
                .thenReturn(Map.of(
                        "schema", "ck3-coat-of-arms-configured-resource-asset-v1",
                        "candidate_id", candidateId));

        given()
                .queryParam("kind", "colored_emblem")
                .queryParam("candidateId", candidateId)
                .when().get("/api/ck3/coat-of-arms/configured-asset")
                .then()
                .statusCode(200)
                .body("schema", equalTo(
                        "ck3-coat-of-arms-configured-resource-asset-v1"))
                .body("candidate_id", equalTo(candidateId));
    }

    @Test
    void probeAndExportKeepTheirTypedMcpArguments() {
        when(mcp.callTool(
                        eq("ck3_probe_coat_of_arms_source_v1"),
                        eq(Map.of(
                                "source", "coa={}",
                                "expected_revision", 0L,
                                "apply", false))))
                .thenReturn(Map.of("status", "detected"));
        when(mcp.callTool(
                        eq("ck3_export_coat_of_arms_source_v1"),
                        eq(Map.of("expected_revision", 0L))))
                .thenReturn(Map.of("status", "exported"));

        given()
                .contentType("application/json")
                .body(Map.of(
                        "source", "coa={}",
                        "expectedRevision", 0,
                        "apply", false))
                .when().post("/api/ck3/coat-of-arms/probe")
                .then().statusCode(200)
                .body("status", equalTo("detected"));
        given()
                .contentType("application/json")
                .body(Map.of("expectedRevision", 0))
                .when().post("/api/ck3/coat-of-arms/export")
                .then().statusCode(200)
                .body("status", equalTo("exported"));

        verify(mcp).callTool(
                "ck3_export_coat_of_arms_source_v1",
                Map.of("expected_revision", 0L));
    }
}
