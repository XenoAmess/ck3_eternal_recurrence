package org.xar.ck3.control.service.mcp;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;

/** Source inventory and Root-owned decisions. A declaration or descriptor grants no dispatch. */
public final class McpCoverage {
    private McpCoverage() { }
    public enum Admission { ADMITTED, EXCLUDED_BY_CURRENT_CONFIGURATION, UNMIGRATED, RETIRED }
    public record Declaration(String name, ExactRef source, int firstLine, int lastLine, String scope, List<String> conditions) {
        public Declaration {
            McpJson.toolName(name); Objects.requireNonNull(source);
            McpJson.require(firstLine > 0 && lastLine >= firstLine && scope != null && !scope.isBlank(), "exact declaration scope required");
            conditions = List.copyOf(conditions);
            for (String condition : conditions) McpJson.require(!condition.isBlank(), "nonempty source condition required");
        }
    }
    public record Catalog(List<Declaration> declarations) {
        public Catalog {
            declarations = List.copyOf(declarations); McpJson.require(!declarations.isEmpty(), "whole declaration catalog required");
            Set<String> names = new HashSet<>();
            for (Declaration declaration : declarations) McpJson.require(names.add(declaration.name()), "duplicate original tool identity");
        }
    }
    public record Decision(String name, Admission admission, ExactRef actualAdmissionProducer, String conditionAndScope) {
        public Decision {
            McpJson.toolName(name); Objects.requireNonNull(admission); Objects.requireNonNull(actualAdmissionProducer);
            McpJson.require(conditionAndScope != null && !conditionAndScope.isBlank(), "source-bound admission condition required");
        }
    }
    public record Report(List<Decision> decisions, int boundTools, int boundResources, boolean completeMigration) {
        public Report {
            decisions = List.copyOf(decisions);
            McpJson.require(boundTools >= 0 && boundTools <= decisions.size() && boundResources >= 0 && boundResources <= 2,
                    "bounded actual MCP coverage counts required");
        }
    }
    public static Catalog readCatalog(RawJson raw) {
        var root = McpJson.object(McpJson.parse(raw.bytes()));
        McpJson.fields(root, Set.of("schema", "sources", "declarations"), Set.of("schema", "sources", "declarations"));
        McpJson.require("xar.original-mcp-declarations/v2".equals(McpJson.text(root.get("schema"))), "catalog schema required");
        McpJson.require(root.get("sources").isArray() && root.get("declarations").isArray(), "catalog arrays required");
        List<ExactRef> sources = new ArrayList<>(); for (var item : root.get("sources")) sources.add(ExactRef.fromJson(item));
        List<Declaration> declarations = new ArrayList<>();
        for (var item : root.get("declarations")) {
            var row = McpJson.object(item);
            McpJson.fields(row, Set.of("name", "source", "line", "end_line", "scope", "conditions"), Set.of("name", "source", "line", "end_line", "scope", "conditions"));
            int index = integer(row.get("source")); McpJson.require(index < sources.size(), "declaration source index out of range");
            McpJson.require(row.get("conditions").isArray(), "declaration conditions array required");
            List<String> conditions = new ArrayList<>(); for (var condition : row.get("conditions")) conditions.add(McpJson.text(condition));
            declarations.add(new Declaration(McpJson.text(row.get("name")), sources.get(index), integer(row.get("line")),
                    integer(row.get("end_line")), McpJson.text(row.get("scope")), conditions));
        }
        return new Catalog(declarations);
    }
    private static int integer(com.fasterxml.jackson.databind.JsonNode value) {
        McpJson.require(value != null && value.isIntegralNumber() && value.canConvertToInt() && value.intValue() >= 0,
                "catalog index/line must be an exact nonnegative integer"); return value.intValue();
    }
}
