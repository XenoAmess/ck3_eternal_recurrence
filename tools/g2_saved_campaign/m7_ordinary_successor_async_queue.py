"""Adapt the existing successor handoff to a caller-owned asynchronous queue.

Importing or constructing this adapter does not operate a queue.  The bounded
Robert demo keeps its existing stop on an actor/episode change; its owner must
explicitly call an adapter method to adopt a successor handoff.  No SDK, Game,
event loop or second queue consumer is created here.

The supplied queue has ``async call(tool, arguments, kind) -> (body, Path)``
and a synchronous or asynchronous ``thin(kind, payload)`` persistence callback.
It must already admit the existing successor tools.  The original demo's
restricted ``generated`` method is not a suitable transport without a separate
owner integration.  Original queue response files remain authoritative.
"""
from __future__ import annotations

import asyncio
import copy
import inspect

from . import m7_ordinary_successor_queue as _successor


class _AsyncQueueFacade:
    """Run unchanged synchronous helpers while their I/O stays on the owner loop."""

    def __init__(self, queue, loop):
        self.queue = queue
        self.loop = loop
        self.stop_requested = False

    async def _invoke(self, method, *args):
        result = getattr(self.queue, method)(*args)
        return await result if inspect.isawaitable(result) else result

    def _dispatch(self, method, *args):
        if self.stop_requested:
            raise RuntimeError("async owner cancelled; no further successor queue calls")
        future = asyncio.run_coroutine_threadsafe(
            self._invoke(method, *args), self.loop
        )
        return future.result()

    def call(self, tool, arguments, kind):
        return self._dispatch("call", tool, arguments, kind)

    def thin(self, kind, payload):
        # Later timeline/SAVE updates must not change an already retained receipt.
        return self._dispatch("thin", kind, copy.deepcopy(payload))


class _RetainedTransitions:
    """Keep the actual completed transition before a subsequent query can fail."""

    def __init__(self, queue, transitions):
        self.queue = queue
        self.transitions = transitions

    def append(self, transition):
        self.transitions.append(transition)
        self.queue.thin("m7-natural-transition-pending", transition)


class AsyncOrdinarySuccessorQueue:
    """Serialize explicit handoffs through the same caller-owned async queue.

    A worker invokes the unchanged synchronous helper.  Every call and receipt
    callback is marshalled back to the caller's existing event loop, and each
    method waits for that helper to finish.  There are no automatic retries.
    The caller must retain the original terminal snapshot and completed AUTO
    response before adopting an already completed continuation.
    """

    def __init__(self, queue):
        if not callable(getattr(queue, "call", None)) or not callable(
            getattr(queue, "thin", None)
        ):
            raise TypeError("successor adapter requires the existing queue call/thin callbacks")
        self.queue = queue
        self._lock = asyncio.Lock()

    async def _run(self, operation):
        async with self._lock:
            facade = _AsyncQueueFacade(self.queue, asyncio.get_running_loop())
            worker = asyncio.create_task(asyncio.to_thread(operation, facade))
            try:
                return await asyncio.shield(worker)
            except asyncio.CancelledError:
                # Collect an already issued request before relinquishing ownership;
                # the helper cannot start another request after cancellation.
                facade.stop_requested = True
                while not worker.done():
                    try:
                        await asyncio.shield(worker)
                    except asyncio.CancelledError:
                        continue
                    except Exception:
                        break
                if worker.done() and not worker.cancelled():
                    worker.exception()
                raise

    async def continue_successor(self, expected_episode, transitions):
        return await self._run(lambda queue: _successor.continue_successor(
            queue, expected_episode, _RetainedTransitions(queue, transitions)
        ))

    async def consume_completed(
        self, turn, response_path, source_snapshot, source_path, transitions,
        checkpoint_pair=None,
    ):
        return await self._run(lambda queue: _successor.consume_completed(
            queue, turn, response_path, source_snapshot, source_path,
            _RetainedTransitions(queue, transitions), checkpoint_pair,
        ))

    async def finish_transition(self, after, after_path, transition, transitions):
        return await self._run(lambda queue: _successor.finish_transition(
            queue, after, after_path, transition,
            _RetainedTransitions(queue, transitions),
        ))

    async def checkpoint_if_clear(self, transition):
        return await self._run(lambda queue: _successor.checkpoint_if_clear(
            queue, transition,
        ))

    async def adopt_successor(
        self, expected_episode, transitions, *, completed_turn=None,
        response_path=None, source_snapshot=None, source_path=None,
        checkpoint_pair=None,
    ):
        """Verify one handoff, then return its SAVE before any later gameplay.

        Supplying ``completed_turn`` consumes that original response without
        submitting Continue again.  Otherwise the existing helper plans and
        executes the matched transition.  A pending player decision returns a
        deferred result; this method does not choose that decision or replay a
        SAVE.  An already checkpointed reference creates no new succession credit.
        """
        if completed_turn is not None and any(value is None for value in (
            response_path, source_snapshot, source_path,
        )):
            raise ValueError("completed handoff requires its original response and terminal snapshot")
        if completed_turn is None and any(value is not None for value in (
            response_path, source_snapshot, source_path, checkpoint_pair,
        )):
            raise ValueError("original response references require the completed continuation")

        def adopt(queue):
            retained = _RetainedTransitions(queue, transitions)
            if completed_turn is None:
                after, after_path, transition = _successor.continue_successor(
                    queue, expected_episode, retained,
                )
            else:
                after, after_path, transition = _successor.consume_completed(
                    queue, completed_turn, response_path, source_snapshot,
                    source_path, retained, checkpoint_pair,
                )
            if transition is None:
                return {
                    "status": "already_checkpointed_reference",
                    "snapshot": after, "snapshot_response": str(after_path),
                    "transition": None,
                    "successor_checkpoint": copy.deepcopy(checkpoint_pair),
                    "save_response": None,
                }
            current, current_path, save_path = _successor.checkpoint_if_clear(
                queue, transition,
            )
            saved = transition["successor_checkpoint"]
            return {
                "status": saved["status"],
                "snapshot": current, "snapshot_response": str(current_path),
                "transition": transition,
                "successor_checkpoint": copy.deepcopy(saved.get("checkpoint")),
                "save_response": str(save_path) if save_path is not None else None,
            }

        return await self._run(adopt)
