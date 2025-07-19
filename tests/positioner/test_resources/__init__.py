import os
from typing import Tuple

import pandas as pd


def load_quaternions(filename: str) -> list[Tuple[float, float, float, float]]:
    current_directory = os.path.dirname(os.path.abspath(__file__))

    df = pd.read_csv(f'{current_directory}/{filename}')
    if list(df.columns) != ['i', 'j', 'k', 'w']:
        raise ValueError(f'Invalid CSV header {df.columns}')
    return df.values.tolist()
