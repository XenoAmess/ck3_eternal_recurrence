package org.xar.ck3.control.wave2.military.combatwire;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;

/** Internal Java domain seam. A production binding must run the complete pinned stock AST evaluator. */
public interface PhaseEventRuntime {
    /** SHA computed by the immutable manifest loader; a wire claim is insufficient. */
    String manifestSha256();
    Set<String> requiredStateRefs();
    /** Evaluate all stock rows, materialization order and feedback coverage; detached JSON result. */
    ObjectNode evaluateContexts(ArrayNode validatedContexts);
}
