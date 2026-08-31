from __future__ import annotations

import unittest
from collections.abc import Iterable

from xar_promo.registry import (
    ADAPTER_ENTRY_POINT_GROUP,
    PRESET_ENTRY_POINT_GROUP,
    ComponentLoadError,
    ComponentNotFoundError,
    ComponentRegistry,
    DuplicateComponentError,
    InvalidComponentFactoryError,
    RegistryError,
)


class CountingFactory:
    def __init__(self, result: object) -> None:
        self.result = result
        self.calls = 0

    def __call__(self, *args: object, **kwargs: object) -> object:
        self.calls += 1
        return self.result


class FakeEntryPoint:
    def __init__(
        self,
        *,
        name: str,
        group: str,
        loaded: object | None = None,
        error: Exception | None = None,
        value: str | None = None,
    ) -> None:
        self.name = name
        self.group = group
        self.value = value or f"fake_plugins:{name}"
        self.loaded = loaded
        self.error = error
        self.load_calls = 0

    def load(self) -> object:
        self.load_calls += 1
        if self.error is not None:
            raise self.error
        return self.loaded


class FakeEntryPoints(list[FakeEntryPoint]):
    def select(self, **filters: str) -> "FakeEntryPoints":
        return FakeEntryPoints(
            item
            for item in self
            if all(getattr(item, key) == value for key, value in filters.items())
        )

    def __init__(self, rows: Iterable[FakeEntryPoint] = ()) -> None:
        super().__init__(rows)


class CountingProvider:
    def __init__(self, rows: Iterable[FakeEntryPoint]) -> None:
        self.rows = FakeEntryPoints(rows)
        self.calls = 0

    def __call__(self) -> FakeEntryPoints:
        self.calls += 1
        return self.rows


class RegistryTests(unittest.TestCase):
    def test_entry_point_group_names_are_stable(self) -> None:
        self.assertEqual("xar_promo.adapters", ADAPTER_ENTRY_POINT_GROUP)
        self.assertEqual("xar_promo.presets", PRESET_ENTRY_POINT_GROUP)

    def test_explicit_local_factories_win_without_discovery_or_invocation(self) -> None:
        adapter = CountingFactory("adapter-result")
        preset = CountingFactory("preset-result")

        def forbidden_provider() -> object:
            raise AssertionError("local resolution must not inspect entry points")

        registry = ComponentRegistry(
            adapters={"local-adapter": adapter},
            presets={"local-preset": preset},
            entry_points_provider=forbidden_provider,
        )

        self.assertIs(adapter, registry.resolve_adapter("local-adapter"))
        self.assertIs(preset, registry.resolve_preset("local-preset"))
        self.assertEqual(0, adapter.calls)
        self.assertEqual(0, preset.calls)

    def test_only_requested_entry_point_is_loaded_and_result_is_cached(self) -> None:
        requested_factory = CountingFactory("requested")
        preset_factory = CountingFactory("preset")
        requested = FakeEntryPoint(
            name="requested",
            group=ADAPTER_ENTRY_POINT_GROUP,
            loaded=requested_factory,
        )
        unrelated_adapter = FakeEntryPoint(
            name="unrelated",
            group=ADAPTER_ENTRY_POINT_GROUP,
            loaded=CountingFactory("unrelated"),
        )
        requested_preset = FakeEntryPoint(
            name="style",
            group=PRESET_ENTRY_POINT_GROUP,
            loaded=preset_factory,
        )
        provider = CountingProvider([requested, unrelated_adapter, requested_preset])
        registry = ComponentRegistry(entry_points_provider=provider)

        self.assertIs(requested_factory, registry.resolve_adapter("requested"))
        self.assertIs(requested_factory, registry.resolve_adapter("requested"))
        self.assertEqual(1, requested.load_calls)
        self.assertEqual(0, unrelated_adapter.load_calls)
        self.assertEqual(0, requested_preset.load_calls)
        self.assertEqual(0, requested_factory.calls)

        self.assertIs(preset_factory, registry.resolve_preset("style"))
        self.assertEqual(1, requested_preset.load_calls)
        self.assertEqual(0, preset_factory.calls)

    def test_duplicate_requested_entry_points_fail_before_loading_either(self) -> None:
        first = FakeEntryPoint(
            name="duplicate",
            group=ADAPTER_ENTRY_POINT_GROUP,
            loaded=CountingFactory("first"),
        )
        second = FakeEntryPoint(
            name="duplicate",
            group=ADAPTER_ENTRY_POINT_GROUP,
            loaded=CountingFactory("second"),
        )
        registry = ComponentRegistry(entry_points_provider=CountingProvider([first, second]))

        with self.assertRaises(DuplicateComponentError) as raised:
            registry.resolve_adapter("duplicate")

        self.assertEqual("adapter", raised.exception.kind)
        self.assertEqual("duplicate", raised.exception.component_id)
        self.assertEqual(0, first.load_calls)
        self.assertEqual(0, second.load_calls)

    def test_unrelated_duplicate_entry_points_do_not_block_requested_id(self) -> None:
        requested_factory = CountingFactory("requested")
        rows = [
            FakeEntryPoint(
                name="requested",
                group=ADAPTER_ENTRY_POINT_GROUP,
                loaded=requested_factory,
            ),
            FakeEntryPoint(
                name="other",
                group=ADAPTER_ENTRY_POINT_GROUP,
                loaded=CountingFactory("other-one"),
            ),
            FakeEntryPoint(
                name="other",
                group=ADAPTER_ENTRY_POINT_GROUP,
                loaded=CountingFactory("other-two"),
            ),
        ]
        registry = ComponentRegistry(entry_points_provider=CountingProvider(rows))

        self.assertIs(requested_factory, registry.resolve_adapter("requested"))
        self.assertEqual([1, 0, 0], [item.load_calls for item in rows])

    def test_duplicate_explicit_registration_has_a_typed_error(self) -> None:
        factory = CountingFactory("adapter")
        with self.assertRaises(DuplicateComponentError) as raised:
            ComponentRegistry(
                adapters=[("same", factory), ("same", factory)],
                discover_entry_points=False,
            )
        self.assertEqual("adapter", raised.exception.kind)
        self.assertEqual("same", raised.exception.component_id)

    def test_local_registration_overrides_same_discovered_id(self) -> None:
        discovered = FakeEntryPoint(
            name="replaceable",
            group=PRESET_ENTRY_POINT_GROUP,
            loaded=CountingFactory("plugin"),
        )
        provider = CountingProvider([discovered])
        registry = ComponentRegistry(entry_points_provider=provider)
        plugin_factory = registry.resolve_preset("replaceable")
        local_factory = CountingFactory("local")

        registry.register_preset("replaceable", local_factory)

        self.assertIsNot(plugin_factory, local_factory)
        self.assertIs(local_factory, registry.resolve_preset("replaceable"))
        self.assertEqual(1, discovered.load_calls)
        self.assertEqual(1, provider.calls)

    def test_missing_component_has_kind_id_and_group(self) -> None:
        registry = ComponentRegistry(entry_points_provider=CountingProvider([]))

        with self.assertRaises(ComponentNotFoundError) as raised:
            registry.resolve_preset("missing")

        self.assertEqual("preset", raised.exception.kind)
        self.assertEqual("missing", raised.exception.component_id)
        self.assertEqual(PRESET_ENTRY_POINT_GROUP, raised.exception.group)

    def test_discovery_can_be_disabled_without_calling_provider(self) -> None:
        calls = 0

        def provider() -> object:
            nonlocal calls
            calls += 1
            return FakeEntryPoints()

        registry = ComponentRegistry(
            discover_entry_points=False,
            entry_points_provider=provider,
        )
        with self.assertRaises(ComponentNotFoundError):
            registry.resolve_adapter("missing")
        self.assertEqual(0, calls)

    def test_discovery_failure_is_wrapped_with_original_cause(self) -> None:
        failure = RuntimeError("metadata unavailable")

        def broken_provider() -> object:
            raise failure

        registry = ComponentRegistry(entry_points_provider=broken_provider)
        with self.assertRaises(ComponentLoadError) as raised:
            registry.resolve_adapter("sample")
        self.assertIs(failure, raised.exception.__cause__)
        self.assertIn("discovery failed", str(raised.exception))

    def test_requested_entry_point_load_failure_is_typed_and_keeps_cause(self) -> None:
        failure = RuntimeError("plugin import failed")
        entry_point = FakeEntryPoint(
            name="broken",
            group=PRESET_ENTRY_POINT_GROUP,
            error=failure,
        )
        registry = ComponentRegistry(entry_points_provider=CountingProvider([entry_point]))

        with self.assertRaises(ComponentLoadError) as raised:
            registry.resolve_preset("broken")

        self.assertEqual("preset", raised.exception.kind)
        self.assertEqual("broken", raised.exception.component_id)
        self.assertIs(failure, raised.exception.__cause__)
        self.assertEqual(1, entry_point.load_calls)

    def test_non_callable_local_or_plugin_value_is_rejected(self) -> None:
        with self.assertRaises(InvalidComponentFactoryError):
            ComponentRegistry(adapters=[("invalid", object())])  # type: ignore[list-item]

        entry_point = FakeEntryPoint(
            name="invalid",
            group=PRESET_ENTRY_POINT_GROUP,
            loaded={"not": "callable"},
        )
        registry = ComponentRegistry(entry_points_provider=CountingProvider([entry_point]))
        with self.assertRaises(InvalidComponentFactoryError):
            registry.resolve_preset("invalid")
        self.assertEqual(1, entry_point.load_calls)

    def test_legacy_mapping_and_plain_iterable_discovery_forms_are_supported(self) -> None:
        mapping_factory = CountingFactory("mapping")
        mapping_ep = FakeEntryPoint(
            name="mapped",
            group=ADAPTER_ENTRY_POINT_GROUP,
            loaded=mapping_factory,
        )
        mapping_registry = ComponentRegistry(
            entry_points_provider=lambda: {ADAPTER_ENTRY_POINT_GROUP: [mapping_ep]}
        )
        self.assertIs(mapping_factory, mapping_registry.resolve_adapter("mapped"))

        iterable_factory = CountingFactory("iterable")
        iterable_ep = FakeEntryPoint(
            name="listed",
            group=PRESET_ENTRY_POINT_GROUP,
            loaded=iterable_factory,
        )
        iterable_registry = ComponentRegistry(entry_points_provider=lambda: [iterable_ep])
        self.assertIs(iterable_factory, iterable_registry.resolve_preset("listed"))

    def test_component_ids_do_not_get_silently_normalized(self) -> None:
        registry = ComponentRegistry(discover_entry_points=False)
        for invalid in ("", "   ", " padded"):
            with self.subTest(invalid=invalid), self.assertRaises(RegistryError):
                registry.resolve_adapter(invalid)


if __name__ == "__main__":
    unittest.main()
