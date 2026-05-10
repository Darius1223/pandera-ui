import nox

PANDERA_VERSIONS = ["0.27.1", "0.31.1"]
PANDAS_VERSIONS = ["2.1.4", "2.2.3", "2.3.3"]

nox.options.default_venv_backend = "uv"


@nox.session(python=["3.10", "3.11", "3.12", "3.13"])
def tests(session: nox.Session) -> None:
    session.run_install("uv", "sync", "--frozen", external=True)
    session.run("pytest", "tests/", "--ignore=tests/test_ui.py", "-q", "--tb=short")


@nox.session(python="3.11", name="compat")
@nox.parametrize("pandera_ver", PANDERA_VERSIONS)
@nox.parametrize("pandas_ver", PANDAS_VERSIONS)
def compat(session: nox.Session, pandera_ver: str, pandas_ver: str) -> None:
    session.install("--no-deps", "-e", ".")
    session.install(
        f"pandera[pandas]=={pandera_ver}",
        f"pandas=={pandas_ver}",
        "fastapi>=0.111",
        "uvicorn[standard]>=0.30",
        "typer>=0.12",
        "pydantic>=2.0",
        "httpx>=0.27",
        "pytest>=8",
    )
    session.run("pytest", "tests/", "--ignore=tests/test_ui.py", "-q", "--tb=short")
