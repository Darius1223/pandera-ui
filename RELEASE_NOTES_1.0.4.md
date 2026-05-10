# pandera-ui 1.0.4

## What's changed

### CI / Dev tooling
- Added `nox` compat matrix — `nox -s compat` tests 6 combinations of pandera × pandas automatically:

  | pandera | pandas 2.1.4 | pandas 2.2.3 | pandas 2.3.3 |
  |---------|:---:|:---:|:---:|
  | 0.27.1  | ✅ | ✅ | ✅ |
  | 0.31.x  | ✅ | ✅ | ✅ |

- CI `compat` job now runs `nox -s compat` instead of hand-rolled pip install steps
- Removed `test_matrix.sh` — superseded by nox

## Run compat matrix locally

```bash
pip install nox
nox -s compat
```
