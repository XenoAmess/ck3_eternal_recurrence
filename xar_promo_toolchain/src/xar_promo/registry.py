"""Lazy, project-neutral adapter and preset factory resolution.

Project manifests intentionally store stable string identifiers.  This module
turns those identifiers into callables without making the generic core import a
particular game adapter or project preset.  Callers may inject local factories
directly; optional Python entry-point discovery is the distribution boundary.

Resolution is deliberately lazy.  Metadata may be filtered to find the
requested identifier, but only that identifier's entry point is ever loaded,
and resolving a factory never invokes the factory itself.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from importlib import metadata
from typing import Any, Literal, Protocol, cast, runtime_checkable

from .errors import PromoToolchainError


ADAPTER_ENTRY_POINT_GROUP = "xar_promo.adapters"
PRESET_ENTRY_POINT_GROUP = "xar_promo.presets"

ComponentKind = Literal["adapter", "preset"]


@runtime_checkable
class AdapterFactory(Protocol):
    """Callable returned for a resolved adapter identifier."""

    def __call__(self, *args: Any, **kwargs: Any) -> object:
        """Create or execute the adapter according to its own public contract."""


@runtime_checkable
class PresetFactory(Protocol):
    """Callable returned for a resolved preset identifier."""

    def __call__(self, *args: Any, **kwargs: Any) -> object:
        """Create or execute the preset according to its own public contract."""


ComponentFactory = AdapterFactory | PresetFactory
RegistrationSource = Mapping[str, ComponentFactory] | Iterable[tuple[str, ComponentFactory]]
EntryPointsProvider = Callable[[], object]


class RegistryError(PromoToolchainError):
    """Base class for actionable adapter/preset resolution failures."""


class DuplicateComponentError(RegistryError):
    """More than one registration claims an identifier in one namespace."""

    def __init__(self, kind: ComponentKind, component_id: str, source: str) -> None:
        self.kind = kind
        self.component_id = component_id
        self.source = source
        super().__init__(
            f"duplicate {kind} id {component_id!r} in {source}; "
            "each id must resolve unambiguously"
        )


class ComponentNotFoundError(RegistryError):
    """No local registration or discoverable entry point has the requested id."""

    def __init__(self, kind: ComponentKind, component_id: str, group: str) -> None:
        self.kind = kind
        self.component_id = component_id
        self.group = group
        super().__init__(
            f"{kind} id {component_id!r} is not registered locally and was not "
            f"found in Python entry-point group {group!r}"
        )


class ComponentLoadError(RegistryError):
    """Discovery or loading failed for the requested component only."""

    def __init__(
        self,
        kind: ComponentKind,
        component_id: str,
        source: str,
        detail: str,
    ) -> None:
        self.kind = kind
        self.component_id = component_id
        self.source = source
        self.detail = detail
        super().__init__(
            f"could not load {kind} id {component_id!r} from {source}: {detail}"
        )


class InvalidComponentFactoryError(ComponentLoadError):
    """A local registration or loaded entry point is not callable."""


class ComponentRegistry:
    """Resolve adapter and preset ids to factories.

    ``adapters`` and ``presets`` accept either mappings or iterables of pairs.
    The iterable form makes accidental duplicate local registrations observable
    rather than silently collapsing them into a dictionary.  Local factories
    always win and completely bypass entry-point discovery for their id.

    The provider injection point exists for deterministic embedding and tests.
    Production callers normally leave it unset and use
    :func:`importlib.metadata.entry_points`.
    """

    def __init__(
        self,
        *,
        adapters: RegistrationSource = (),
        presets: RegistrationSource = (),
        discover_entry_points: bool = True,
        entry_points_provider: EntryPointsProvider | None = None,
    ) -> None:
        self._local: dict[ComponentKind, dict[str, ComponentFactory]] = {
            "adapter": {},
            "preset": {},
        }
        self._loaded: dict[ComponentKind, dict[str, ComponentFactory]] = {
            "adapter": {},
            "preset": {},
        }
        self._discover_entry_points = discover_entry_points
        self._entry_points_provider = entry_points_provider
        self._register_many("adapter", adapters)
        self._register_many("preset", presets)

    def register_adapter(self, component_id: str, factory: AdapterFactory) -> None:
        """Register one explicit adapter factory."""

        self._register("adapter", component_id, factory)

    def register_preset(self, component_id: str, factory: PresetFactory) -> None:
        """Register one explicit preset factory."""

        self._register("preset", component_id, factory)

    def resolve_adapter(self, component_id: str) -> AdapterFactory:
        """Return, but do not invoke, the requested adapter factory."""

        return cast(AdapterFactory, self._resolve("adapter", component_id))

    def resolve_preset(self, component_id: str) -> PresetFactory:
        """Return, but do not invoke, the requested preset factory."""

        return cast(PresetFactory, self._resolve("preset", component_id))

    def _register_many(
        self,
        kind: ComponentKind,
        registrations: RegistrationSource,
    ) -> None:
        rows = registrations.items() if isinstance(registrations, Mapping) else registrations
        for component_id, factory in rows:
            self._register(kind, component_id, factory)

    def _register(
        self,
        kind: ComponentKind,
        component_id: str,
        factory: ComponentFactory,
    ) -> None:
        normalized = self._component_id(kind, component_id)
        if normalized in self._local[kind]:
            raise DuplicateComponentError(kind, normalized, "the explicit local registry")
        if not callable(factory):
            raise InvalidComponentFactoryError(
                kind,
                normalized,
                "the explicit local registry",
                f"expected a callable factory, got {type(factory).__name__}",
            )
        self._local[kind][normalized] = factory

    def _resolve(self, kind: ComponentKind, component_id: str) -> ComponentFactory:
        normalized = self._component_id(kind, component_id)

        # This check intentionally precedes both the cache and metadata access.
        # A late local injection still overrides a previously discovered plugin.
        local = self._local[kind].get(normalized)
        if local is not None:
            return local

        cached = self._loaded[kind].get(normalized)
        if cached is not None:
            return cached

        group = self._group(kind)
        if not self._discover_entry_points:
            raise ComponentNotFoundError(kind, normalized, group)

        candidates = self._select_entry_points(kind, normalized, group)
        if not candidates:
            raise ComponentNotFoundError(kind, normalized, group)
        if len(candidates) > 1:
            raise DuplicateComponentError(kind, normalized, f"entry-point group {group!r}")

        entry_point = candidates[0]
        source = self._entry_point_source(entry_point, group, normalized)
        try:
            loaded = entry_point.load()
        except Exception as exc:
            raise ComponentLoadError(kind, normalized, source, str(exc) or type(exc).__name__) from exc
        if not callable(loaded):
            raise InvalidComponentFactoryError(
                kind,
                normalized,
                source,
                f"entry point returned non-callable {type(loaded).__name__}",
            )

        factory = cast(ComponentFactory, loaded)
        self._loaded[kind][normalized] = factory
        return factory

    def _select_entry_points(
        self,
        kind: ComponentKind,
        component_id: str,
        group: str,
    ) -> tuple[Any, ...]:
        provider = self._entry_points_provider or metadata.entry_points
        try:
            discovered = provider()
            selector = getattr(discovered, "select", None)
            if callable(selector):
                selected = selector(group=group, name=component_id)
            elif isinstance(discovered, Mapping):
                selected = (
                    item
                    for item in discovered.get(group, ())
                    if getattr(item, "name", None) == component_id
                )
            else:
                selected = (
                    item
                    for item in cast(Iterable[object], discovered)
                    if getattr(item, "group", None) == group
                    and getattr(item, "name", None) == component_id
                )
            return tuple(selected)
        except Exception as exc:
            raise ComponentLoadError(
                kind,
                component_id,
                f"entry-point group {group!r}",
                f"discovery failed: {str(exc) or type(exc).__name__}",
            ) from exc

    @staticmethod
    def _component_id(kind: ComponentKind, component_id: str) -> str:
        if not isinstance(component_id, str) or not component_id.strip():
            raise RegistryError(f"{kind} id must be a non-empty string")
        normalized = component_id.strip()
        if normalized != component_id:
            raise RegistryError(f"{kind} id must not contain surrounding whitespace")
        return normalized

    @staticmethod
    def _group(kind: ComponentKind) -> str:
        if kind == "adapter":
            return ADAPTER_ENTRY_POINT_GROUP
        return PRESET_ENTRY_POINT_GROUP

    @staticmethod
    def _entry_point_source(entry_point: object, group: str, component_id: str) -> str:
        value = getattr(entry_point, "value", None)
        if isinstance(value, str) and value:
            return f"entry point {group}:{component_id} ({value})"
        return f"entry point {group}:{component_id}"


__all__ = [
    "ADAPTER_ENTRY_POINT_GROUP",
    "PRESET_ENTRY_POINT_GROUP",
    "AdapterFactory",
    "PresetFactory",
    "ComponentRegistry",
    "RegistryError",
    "DuplicateComponentError",
    "ComponentNotFoundError",
    "ComponentLoadError",
    "InvalidComponentFactoryError",
]
