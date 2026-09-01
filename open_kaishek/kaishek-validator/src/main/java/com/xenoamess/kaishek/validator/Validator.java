package com.xenoamess.kaishek.validator;

import com.xenoamess.kaishek.profile.*;
import com.xenoamess.kaishek.syntax.*;
import java.util.*;

/** Strict, schema-aware validator. It only reports diagnostics; it never rewrites CST. */
public final class Validator {
    private Validator() {}

    public static List<Diagnostic> validate(ParseResult parsed, String sourcePath, KaishekProfile profile) {
        Objects.requireNonNull(parsed);
        var result = new ArrayList<Diagnostic>();
        for (var d : parsed.diagnostics())
            result.add(new Diagnostic(d.code(), Diagnostic.Severity.valueOf(d.severity().name()), d.message(), sourcePath, d.span()));
        result.addAll(validate(parsed.document(), sourcePath, profile));
        return List.copyOf(result);
    }
    public static List<Diagnostic> validate(Document document, String sourcePath, KaishekProfile profile) {
        Objects.requireNonNull(document); Objects.requireNonNull(profile);
        List<Diagnostic> out = new ArrayList<>();
        ScriptDomain domain = profile.domainForPath(sourcePath);
        if (domain == ScriptDomain.UNKNOWN)
            out.add(diag("UNKNOWN_DIRECTORY", Diagnostic.Severity.ERROR, "no schema profile for directory", document.span(), sourcePath));
        walk(document.children(), domain, profile, out, sourcePath, 0);
        return List.copyOf(out);
    }
    /** Profile-api entry point; keeps validator independent of concrete profile modules. */
    public static List<Diagnostic> validate(ParseResult parsed, String sourcePath, GameProfile profile) {
        return validate(parsed, sourcePath, KaishekProfile.fromGameProfile(profile));
    }
    private static void walk(List<CstNode> nodes, ScriptDomain domain, KaishekProfile profile, List<Diagnostic> out, String path, int depth) {
        Map<String, EntryNode> seen = new HashMap<>();
        for (CstNode n : nodes) {
            if (!(n instanceof EntryNode e)) continue;
            // GUI declaration headers such as `types Foo {}` and
            // `blockoverride "name" {}` intentionally have no `=` operator.
            // Their nested widget vocabulary is outside the Phase 0 semantic
            // opcode table; parser diagnostics still cover malformed syntax,
            // so do not misclassify these declarations as unknown opcodes.
            if (domain == ScriptDomain.GUI_REGISTRATION && e.operator() == null) continue;
            String key = e.key().text().trim();
            String at = path + "." + key;
            // A file-root block is a declaration map, where duplicate names
            // can hide an earlier definition.  Nested CK3 blocks are ordered
            // executable sequences (and may intentionally repeat an opcode),
            // so do not apply map-duplicate semantics to them.
            if (depth == 0 && seen.putIfAbsent(key, e) != null)
                out.add(diag("DUPLICATE_KEY", Diagnostic.Severity.ERROR, "duplicate key in the same block: " + key, e.span(), at));
            OpcodeSpec spec = profile.opcode(key);
            boolean opcodePosition = depth > 0;
            boolean scalarRootOpcode = depth == 0 && !(e.value() instanceof BlockNode) &&
                    (domain == ScriptDomain.SCRIPTED_EFFECTS || domain == ScriptDomain.SCRIPTED_TRIGGERS || domain == ScriptDomain.SCRIPTED_VALUES);
            if ((opcodePosition || scalarRootOpcode) && spec == null && !profile.allowedStructuralKeys().contains(key))
                out.add(diag("UNKNOWN_OPCODE", Diagnostic.Severity.ERROR, "unregistered opcode: " + key, e.key().span(), at));
            // A registered opcode is unambiguous even at file root; declarations
            // (event/scripted-effect IDs) are simply absent from the registry.
            if (spec != null) {
                validateDomain(spec, domain, e, out, at);
                validateParameters(spec, e, out, at);
                validateScope(spec, e, out, at);
            }
            if (e.value() instanceof BlockNode b) {
                // A registered non-structural opcode owns its RHS block as a
                // typed argument object (`name = { ... }`, `flag = { ... }`,
                // etc.).  Walking those fields as executable opcodes would
                // report every parameter name as UNKNOWN_OPCODE and would
                // make a valid CST→IR slice impossible.  Structural control
                // words such as `random` still recurse because their block is
                // an executable child sequence rather than a parameter map.
                boolean argumentBlock = spec != null
                        && spec.kind() != OpcodeSpec.Kind.STRUCTURAL
                        && spec.kind() != OpcodeSpec.Kind.INTERFACE;
                if (!argumentBlock) walk(b.children(), domain, profile, out, at, depth + 1);
            }
        }
    }
    private static void validateDomain(OpcodeSpec spec, ScriptDomain domain, EntryNode e, List<Diagnostic> out, String path) {
        boolean trigger = domain == ScriptDomain.SCRIPTED_TRIGGERS;
        boolean effect = domain == ScriptDomain.SCRIPTED_EFFECTS || domain == ScriptDomain.ON_ACTION;
        boolean value = domain == ScriptDomain.SCRIPTED_VALUES;
        if ((trigger && spec.kind() == OpcodeSpec.Kind.EFFECT) || (effect && spec.kind() == OpcodeSpec.Kind.TRIGGER) ||
            (value && spec.kind() != OpcodeSpec.Kind.VALUE && spec.kind() != OpcodeSpec.Kind.STRUCTURAL))
            out.add(diag("WRONG_DOMAIN", Diagnostic.Severity.ERROR, "opcode " + spec.name() + " is " + spec.kind() + " but file domain is " + domain, e.key().span(), path));
    }
    private static void validateParameters(OpcodeSpec spec, EntryNode e, List<Diagnostic> out, String path) {
        if (!(e.value() instanceof BlockNode b)) return;
        List<EntryNode> parameters = new ArrayList<>();
        for (EntryNode parameter : b.entries()) {
            String name = parameter.key().text().trim();
            // CK3 parameter blocks are ordered and may legally repeat a
            // named field (for example, repeated value/add terms).  Keep
            // every occurrence for arity/declared-name checks; duplicate
            // diagnostics belong only to executable/structural sibling
            // sequences in walk(), where a repeated key is ambiguous.
            if (!name.equals("scope")) parameters.add(parameter);
        }
        Set<String> declared = spec.parameterNames();
        if (!declared.isEmpty()) {
            for (EntryNode parameter : parameters) {
                String name = parameter.key().text().trim();
                if (!declared.contains(name)) {
                    out.add(diag("INVALID_PARAMETERS", Diagnostic.Severity.ERROR,
                            "parameter " + name + " is not declared by opcode " + spec.name(),
                            parameter.key().span(), path + "." + name));
                }
            }
        }
        int count = parameters.size();
        if (count < spec.minParameters() || count > spec.maxParameters())
            out.add(diag("INVALID_PARAMETERS", Diagnostic.Severity.ERROR, "opcode " + spec.name() + " expects " + spec.minParameters() + ".." + (spec.maxParameters() == Integer.MAX_VALUE ? "*" : spec.maxParameters()) + " parameters, got " + count, e.value().span(), path));
    }
    private static void validateScope(OpcodeSpec spec, EntryNode e, List<Diagnostic> out, String path) {
        if (spec.allowedScopes().isEmpty() || !(e.value() instanceof BlockNode b)) return;
        for (EntryNode child : b.entries()) if (child.key().text().trim().equals("scope") && child.value() != null) {
            String scope = child.value().text().trim();
            if (!spec.allowedScopes().contains(scope)) out.add(diag("INVALID_SCOPE", Diagnostic.Severity.ERROR, "scope " + scope + " is not valid for " + spec.name(), child.value().span(), path + ".scope"));
        }
    }
    private static Diagnostic diag(String c, Diagnostic.Severity s, String m, SourceSpan span, String p) { return new Diagnostic(c, s, m, p, span); }
}
