import os
import pandas as pd
from modelstar.connectors.snowflake.context import SnowflakeContext
from modelstar.connectors.snowflake.context_types import FileFormat, SnowflakeConfig
from modelstar.executors.table import table_info_from_csv


def create_table(config, file_path: str, table_name: str = None):
    # TODO: get the file attributes and types using a dataframe. after loading csv.
    # create a file format in the stage: csv_file_name
    # copy the data into the table from the file.
    _, file_extension = os.path.splitext(file_path)

    if file_extension == '.csv':
        table_info = table_info_from_csv(
            file_path=file_path, table_name=table_name)
        file_format = create_file_format(file_name=os.path.basename(file_path))
    else:
        raise ValueError(f'`{file_extension}` is not supported or is invalid.')

    if isinstance(config, SnowflakeConfig):
        snowflake_context = SnowflakeContext(config)
        response = snowflake_context.create_table_from_csv(
            file_path=file_path, table_info=table_info, file_format=file_format)
    else:
        raise ValueError(f'Failed to upload file: {file_path}')

    return response.table.print()


def create_file_format(file_name: str, format_type: str = 'csv', format_name: str = None, delimiter: str = ',', skip_header: int = 1) -> FileFormat:
    file_basename, file_extension = os.path.splitext(file_name)

    if format_name == None:
        format_name = format_type + '_' + file_basename

    return FileFormat(format_name=format_name, format_type=format_type, delimiter=delimiter, skip_header=skip_header)
