"""Typer-based CLI for the JS-RE-Bench platform."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="bench",
    help="JS-RE-Bench command-line interface.",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)
dim_app = typer.Typer(name="dimensions", help="Manage evaluation dimensions.")
sample_app = typer.Typer(name="samples", help="Manage samples.")
app.add_typer(dim_app)
app.add_typer(sample_app)

console = Console()


@app.command()
def version() -> None:
    """Print the platform version."""
    from benchmark import __version__

    console.print(f"js-re-bench {__version__}")


@app.command()
def run(
    dimension: str = typer.Option(..., "--dimension", "-d", help="Dimension code, e.g. D01"),
    model: str = typer.Option(
        "mock/echo-v1",
        "--model",
        "-m",
        help="Model id (mock/*, anthropic/*, openai/*)",
    ),
    sample_id: str | None = typer.Option(
        None,
        "--sample-id",
        "-s",
        help="Sample variant UUID. If omitted, the first seed sample is used.",
    ),
    seed: int = typer.Option(42, "--seed", help="Deterministic seed"),
    out: Path | None = typer.Option(None, "--out", "-o", help="Write JSON result to path"),
    execute: bool = typer.Option(
        False, "--execute/--no-execute", help="Run the pipeline end-to-end"
    ),
) -> None:
    """Submit a benchmark run. With ``--execute`` runs the pipeline synchronously."""

    payload = asyncio.run(_run_pipeline(dimension, model, sample_id, seed, execute))
    text = json.dumps(payload, indent=2, ensure_ascii=False, default=str)
    console.print_json(text)
    if out:
        out.write_text(text, encoding="utf-8")


async def _resolve_sample(dimension: str, sample_id: str | None):
    from apps.api.container import get_artifact_store
    from benchmark.samples.loader import SampleLoader

    loader = SampleLoader(get_artifact_store())
    pairs = await loader.load_dimension(Path("benchmark/samples/seed_samples").resolve(), dimension)
    if not pairs:
        console.print(
            f"[yellow]No samples found for {dimension}. "
            "Drop a sample under benchmark/samples/seed_samples/<DIM>/<name>/ first.[/yellow]"
        )
        raise typer.Exit(code=1)
    if sample_id is not None:
        target = next((p for p in pairs if str(p[1].id) == sample_id), None)
        if target is None:
            console.print(f"[red]Sample {sample_id} not found in {dimension}.[/red]")
            raise typer.Exit(code=2)
    else:
        target = pairs[0]
    return target


async def _run_pipeline(
    dimension: str, model: str, sample_id: str | None, seed: int, execute: bool
) -> dict:
    from apps.api.container import build_dimension, get_model, get_run_service
    from benchmark.core.domain import RunSpec

    target = await _resolve_sample(dimension, sample_id)
    _family, variant = target

    service = get_run_service()
    spec = RunSpec(
        sample_variant_id=variant.id,
        dimension_code=dimension,
        model_id=model,
        seed=seed,
    )
    record = await service.submit(spec)

    if not execute:
        return record.model_dump(mode="json")

    dim_obj = build_dimension(dimension)
    if dim_obj is None:
        console.print(f"[red]Dimension {dimension} not found in registry.[/red]")
        return record.model_dump(mode="json")

    final = await service.execute(
        record.id,
        dimension=dim_obj,
        sample=variant,
        model=get_model(model),
    )
    return final.model_dump(mode="json")


@dim_app.command("list")
def dim_list() -> None:
    """List all 18 evaluation dimensions."""
    from apps.api.container import get_dimension_registry

    registry = get_dimension_registry()
    table = Table(title="Evaluation Dimensions", show_lines=False)
    table.add_column("Code", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Papers", style="yellow")
    for code in sorted(registry):
        cls = registry[code]
        table.add_row(code, cls.name, ", ".join(cls.paper_refs) or "-")
    console.print(table)


@sample_app.command("list")
def samples_list(
    dimension: str = typer.Option("D01", "--dimension", "-d"),
) -> None:
    """List loaded samples for a dimension."""

    async def _run() -> list[dict]:
        from apps.api.container import get_artifact_store
        from benchmark.samples.loader import SampleLoader

        loader = SampleLoader(get_artifact_store())
        pairs = await loader.load_dimension(
            Path("benchmark/samples/seed_samples").resolve(), dimension
        )
        return [
            {
                "family": fam.name,
                "level": v.obfuscation_level.value,
                "variant_id": str(v.id),
                "obfuscator": v.obfuscator,
            }
            for fam, v in pairs
        ]

    rows = asyncio.run(_run())
    if not rows:
        console.print(f"[yellow]No samples loaded for {dimension}.[/yellow]")
        return
    table = Table(title=f"{dimension} Samples")
    for col in ("family", "level", "variant_id", "obfuscator"):
        table.add_column(col, no_wrap=False)
    for r in rows:
        table.add_row(r["family"], r["level"], r["variant_id"], r["obfuscator"] or "-")
    console.print(table)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
