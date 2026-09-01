# kaishek-runtime

Pure-Java Phase 3 kernel primitives. The module has no Quarkus or persistence
dependency. `ScopeContext` keeps typed ROOT/THIS/PREV references, `CaseRegistry`
and `DeadlineTicket` bind delayed work to a serial/owner/subject/revision, and
`ReceiptJournal` applies debits/refunds while enforcing conservation. Randomness
is consumed only from an explicit finite `DrawTape`; exhaustion is converted to
an `UNSUPPORTED` result by `RuntimeKernel`/`HookDispatcher`.

```java
var owner = new ScopeRef(ScopeType.CHARACTER, "c1");
var ctx = new ExecutionContext(new ScopeContext(owner, owner, null), 0,
                               DrawTape.of(3, 9));
```

Unregistered or uncertified opcodes and hooks never become silent no-ops. They
return `ExecutionStatus.UNSUPPORTED` with a trace entry. `ExecutionTrace` keeps
ordered operations plus read/write sets for differential replay.
