package com.xenoamess.ck3coa;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.equalTo;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import io.quarkus.test.InjectMock;
import io.quarkus.test.junit.QuarkusTest;
import java.util.Map;
import org.junit.jupiter.api.Test;

@QuarkusTest
class CoatOfArmsResourceTest {
    @InjectMock
    CoatOfArmsMcpClient mcp;

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
