# Release Notes — pandera-ui 1.1.0

## New flags

### `--version`
```bash
pandera-ui --version
# pandera-ui 1.1.0
```

### `--verbose` / `-v`
Shows per-file progress during scanning — which extraction method was used and how many schemas were found:
```bash
pandera-ui . --verbose
#   runtime            data/orders.py  (1 schema(s))
#   ast[fallback]      data/broken.py  (0 schema(s))
```

### `--workers N`
Parallel scanning with N threads. Speeds up projects with many Python files where import time is the bottleneck:
```bash
pandera-ui . --workers 4
```

### `--no-import`
AST-only mode — skips dynamic import entirely. Faster and no risk of side-effects from importing project code:
```bash
pandera-ui . --no-import
```

## Bug fix: transitive DataFrameModel subclasses in AST mode

The AST extractor previously only detected direct subclasses of `pa.DataFrameModel`. Classes inheriting from a custom intermediate model were silently skipped.

```python
class MyBase(pa.DataFrameModel):
    x: Series[int]

class Child(MyBase):   # ← was missed before, now found
    y: Series[str]
```

Both `MyBase` and `Child` are now discovered in AST mode.
