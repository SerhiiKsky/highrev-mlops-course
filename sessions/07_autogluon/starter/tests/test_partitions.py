import pandas as pd
import pytest

from lab07.contracts import FEATURES, TARGET
from lab07.train import read_partition


def test_boolean_target_is_normalized_to_integer_labels(tmp_path):
    path = tmp_path / 'partition.csv'
    rows = [
        ['row-1', 3, 30, 'F', True, 'PL', 'Chrome', 'Windows', False],
        ['row-2', 4, 25, 'M', False, 'PL', 'Firefox', 'Linux', True],
    ]
    pd.DataFrame(rows, columns=['row_id', *FEATURES, TARGET]).to_csv(path, index=False)
    result = read_partition(path)
    assert result[TARGET].tolist() == [0, 1]
    assert result[TARGET].dtype.kind in 'iu'


def test_partition_with_one_class_is_rejected(tmp_path):
    path = tmp_path / 'partition.csv'
    pd.DataFrame([['row-1', 3, 30, 'F', True, 'PL', 'Chrome', 'Windows', False]],
                 columns=['row_id', *FEATURES, TARGET]).to_csv(path, index=False)
    with pytest.raises(ValueError, match='Both binary labels'):
        read_partition(path)
