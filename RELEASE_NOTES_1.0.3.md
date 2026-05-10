# pandera-ui 1.0.3

## What's changed

### Fixed
- Frontend assets (`index.html`, JS, CSS) are now correctly bundled into the wheel and found after `pip install` ([ed6826e](https://github.com/darius-krsk/pandera-ui/commit/ed6826e))

### Dependencies
- Relaxed `pandera` lower bound from `>=0.19` to `>=0.27.1` — reflects the actual minimum where `pandera.pandas` is available and `DataFrameModel.to_schema()` works correctly with NumPy 2.x
- Relaxed `pandas` lower bound from `>=2.3.3` to `>=2.1.1` — pandas 2.1.x, 2.2.x, and 2.3.x are all supported
- Removed explicit `numpy` pin — numpy is a transitive dependency resolved by pandera/pandas

### CI
- Added `compat` job: runs the full test suite against minimum supported versions (`pandera==0.27.1`, `pandas==2.1.1`, Python 3.10) on every push

## Compatibility matrix

Verified via automated 4×4 matrix test (`test_matrix.sh`):

| pandera | pandas 2.1.x | pandas 2.2.x | pandas 2.3.x |
|---------|:---:|:---:|:---:|
| 0.27.1  | ✅ | ✅ | ✅ |
| 0.31.x  | ✅ | ✅ | ✅ |

Requires Python 3.10+.
