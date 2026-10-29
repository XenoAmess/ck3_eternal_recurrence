package org.xar.ck3.control.wave2.runtime.providerchain;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure syntax/comparison leaf; returned process and file identity remain outside this value. */
public record DirectScriptCommand(List<String> argv) {
    private static final Set<String> FLAGS = Set.of("-B", "-u", "-S", "-X");

    public record ResolvedOperand(int index, String originalOperand, String resolvedPath) {
        public ResolvedOperand {
            StrictJson.require(index >= 1, "actual script operand index required");
            CreatorSourceManifest.requireAbsoluteWindows(originalOperand);
            CreatorSourceManifest.requireAbsoluteWindows(resolvedPath);
        }
    }

    public record Inspection(int scriptOperandIndex, String executable, String resolvedEntry) {
        public Inspection {
            StrictJson.require(scriptOperandIndex >= 1, "script operand index required");
            CreatorSourceManifest.requireAbsoluteWindows(executable);
            CreatorSourceManifest.requireAbsoluteWindows(resolvedEntry);
        }
        public boolean grantsProcessOrProviderQualification() { return false; }
    }

    public DirectScriptCommand {
        StrictJson.require(argv != null && argv.size() >= 2, "exact direct Python script command required");
        ArrayList<String> copy = new ArrayList<>(argv);
        for (String argument : copy) {
            StrictJson.require(argument != null, "actual argv text required");
            if (!argument.isEmpty()) { StrictJson.text(argument); }
        }
        CreatorSourceManifest.requireAbsoluteWindows(copy.getFirst());
        argv = List.copyOf(copy);
    }

    public Inspection inspect(String frozenEntry, ResolvedOperand observed) {
        CreatorSourceManifest.requireAbsoluteWindows(frozenEntry);
        int index = scriptOperandIndex();
        StrictJson.require(observed != null && observed.index() == index
                        && observed.originalOperand().equals(argv.get(index)) && observed.resolvedPath().equals(frozenEntry),
                "actual Python script operand is not the frozen entry");
        return new Inspection(index, argv.getFirst(), observed.resolvedPath());
    }

    /** Locate before calling the existing strict resolver; do not repeat this scan in an adapter. */
    public int scriptOperandIndex() {
        int index = 1; HashSet<String> seen = new HashSet<>();
        while (index < argv.size() && argv.get(index).startsWith("-")) {
            String flag = argv.get(index);
            StrictJson.require(FLAGS.contains(flag) && seen.add(flag), "unsupported Python interpreter flag or execution mode");
            index++;
            if (flag.equals("-X")) {
                StrictJson.require(index < argv.size() && argv.get(index).equals("utf8"),
                        "only the frozen Python utf8 interpreter option is supported");
                index++;
            }
        }
        StrictJson.require(index < argv.size(), "actual Python script operand is not the frozen entry");
        CreatorSourceManifest.requireAbsoluteWindows(argv.get(index));
        return index;
    }
}
