package com.xenoamess.kaishek.ir;

import java.util.*;

public sealed interface IrValue permits IrValue.LiteralValue, IrValue.VariableRef, IrValue.ScopeRef, IrValue.ListValue {
    record LiteralValue(Object value) implements IrValue {
        public LiteralValue {
            if (value != null && !(value instanceof String || value instanceof Number || value instanceof Boolean))
                throw new IllegalArgumentException("literal must be string, number, boolean or null");
            if (value instanceof Double d && !Double.isFinite(d))
                throw new IllegalArgumentException("literal number must be finite");
            if (value instanceof Float f && !Float.isFinite(f))
                throw new IllegalArgumentException("literal number must be finite");
        }
    }
    record VariableRef(String name) implements IrValue {
        public VariableRef { if (name == null || name.isBlank()) throw new IllegalArgumentException("name is blank"); }
    }
    record ScopeRef(String name) implements IrValue {
        public ScopeRef { if (name == null || name.isBlank()) throw new IllegalArgumentException("name is blank"); }
    }
    record ListValue(List<IrValue> values) implements IrValue {
        public ListValue { values = List.copyOf(Objects.requireNonNull(values, "values")); }
    }
}
