"""``paa`` command line: fetch sources, load them, build derived data, serve the API."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer

from paa.config import get_settings

app = typer.Typer(no_args_is_help=True, help="Property Acquisition Analyser pipeline and API.")
db_app = typer.Typer(no_args_is_help=True, help="Database schema.")
app.add_typer(db_app, name="db")
dev_app = typer.Typer(
    no_args_is_help=True, help="Development-only helpers. Never run in production."
)
app.add_typer(dev_app, name="dev")


@app.callback()
def _setup(verbose: Annotated[bool, typer.Option("-v", help="Debug logging")] = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@db_app.command("migrate")
def db_migrate() -> None:
    """Create or upgrade the schema."""
    from paa.etl.migrate import migrate

    migrate()


@app.command()
def fetch(
    ppd_year: Annotated[
        int | None, typer.Option(help="Download one PPD year instead of the complete file")
    ] = None,
    ppd_complete: Annotated[
        bool, typer.Option(help="Download the ~5.5 GB complete PPD file")
    ] = False,
    ppd_monthly: Annotated[
        bool, typer.Option(help="Download the latest PPD monthly update")
    ] = False,
    uprn: Annotated[str | None, typer.Option(help="PPD UPRN lookup month, e.g. 2026-08")] = None,
    force: Annotated[bool, typer.Option(help="Re-download even if present")] = False,
) -> None:
    """Download Code-Point Open, the latest UK HPI, and the PPD files requested."""
    from paa.etl import sources

    sources.download(sources.codepoint_open(), force=force)
    sources.download(sources.latest_hpi(), force=force)
    if ppd_year:
        sources.download(sources.ppd_year(ppd_year), force=force)
    if ppd_complete:
        sources.download(sources.ppd_complete(), force=force)
    if ppd_monthly:
        sources.download(sources.ppd_monthly(), force=force)
    if uprn:
        y, m = (int(x) for x in uprn.split("-"))
        sources.download(sources.ppd_uprn_lookup(y, m), force=force)


@app.command("load-postcodes")
def load_postcodes() -> None:
    """Load Code-Point Open postcode centroids."""
    from paa.etl import postcodes, sources

    postcodes.load(sources.codepoint_open().path)


@app.command("load-hpi")
def load_hpi(
    file: Annotated[
        Path | None, typer.Option(help="Specific HPI full file; default newest in data dir")
    ] = None,
) -> None:
    """Load the UK House Price Index."""
    from paa.etl import hpi

    path = file or _newest(get_settings().data_dir / "hpi", "UK-HPI-full-file-*.csv")
    hpi.load(path)


@app.command("load-ppd")
def load_ppd(
    file: Annotated[Path, typer.Argument(help="PPD CSV (complete, yearly or monthly update)")],
    replace: Annotated[
        bool, typer.Option(help="Truncate core.sale first (use for the complete file)")
    ] = False,
) -> None:
    """Load a Price Paid Data file."""
    from paa.etl import ppd

    ppd.load(file, replace=replace)


@app.command("load-uprn")
def load_uprn(
    file: Annotated[Path, typer.Argument(help="pp-uprn-lookup-<mon>-<year>.csv")],
) -> None:
    """Load a PPD transaction -> UPRN lookup."""
    from paa.etl import ppd

    ppd.load_uprn_lookup(file)


@app.command("load-epc")
def load_epc(
    root: Annotated[
        Path | None, typer.Option(help="Folder containing certificates*.csv files")
    ] = None,
) -> None:
    """Load EPC certificates from files under <data_dir>/epc."""
    from paa.etl import epc

    epc.load(root or get_settings().data_dir / "epc")


@app.command()
def build(
    step: Annotated[
        list[str] | None, typer.Option(help="Only steps whose filename starts with this, e.g. 030")
    ] = None,
) -> None:
    """Match sales to EPCs, enrich, aggregate cells and (re)define tile functions."""
    from paa.etl.migrate import build as run_build

    run_build(step)


@app.command()
def serve(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: Annotated[bool, typer.Option(help="Auto-reload on code changes")] = False,
) -> None:
    """Run the HTTP API."""
    import uvicorn

    uvicorn.run("paa.api.app:create_app", factory=True, host=host, port=port, reload=reload)


@dev_app.command("synth-epc")
def dev_synth_epc() -> None:
    """Insert FAKE EPC certificates (made-up floor areas) so the pipeline runs without real data."""
    from paa.etl import synth

    typer.secho(
        "Generating SYNTHETIC floor areas. Nothing derived from these is real.", fg="yellow"
    )
    synth.generate()


@dev_app.command("drop-synth")
def dev_drop_synth() -> None:
    """Remove synthetic EPC certificates."""
    from paa.etl import synth

    synth.drop()


def _newest(folder: Path, pattern: str) -> Path:
    files = sorted(folder.glob(pattern))
    if not files:
        raise typer.BadParameter(f"no {pattern} in {folder}; run `paa fetch` first")
    return files[-1]


if __name__ == "__main__":
    app()
