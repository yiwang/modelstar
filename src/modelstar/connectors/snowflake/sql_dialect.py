from modelstar.executors.py_parser.module_function import ModuleFunction
from modelstar.executors.table import TableInfo
from modelstar.connectors.snowflake.context_types import SnowflakeConfig, FileFormat
import os


def session_use(config: SnowflakeConfig):
    database = config.database
    schema = config.schema
    stage = config.stage

    sql_statements = []
    sql_statements.append(f'USE {database}.{schema};')

    return sql_statements


def register_udf_from_file(config: SnowflakeConfig, file_path: str, function: ModuleFunction, imports: list, package_imports: list, version: str):

    stage = config.stage
    file_name = os.path.basename(file_path)

    import_list = [f"'{x}'" for x in imports]
    import_list.append(f"'@{stage}/{function.name}/{version}/{file_name}'")
    import_list_string = ', '.join(import_list)

    package_list = [f"'{x}'" for x in package_imports]
    package_list_string = ', '.join(package_list)

    sql_statements = []

    sql_statements.append(
        f'put file://{file_path} @{stage}/{function.name}/{version}')
    sql_statements.append(f"""create or replace function {function.name}({function.sql_param_list()})
returns {function.returns.sql_type()}
language python
runtime_version = '3.8'
packages = ({package_list_string})
handler = '{function.module_name}.{function.name}'
imports = ({import_list_string});""")

    return sql_statements


def register_procedure_from_file(config: SnowflakeConfig, file_path: str, function: ModuleFunction, imports: list, package_imports: list, version: str):

    stage = config.stage
    file_name = os.path.basename(file_path)

    import_list = [f"'{x}'" for x in imports]
    import_list.append(f"'@{stage}/{function.name}/{version}/{file_name}'")
    import_list_string = ', '.join(import_list)

    package_list = [f"'{x}'" for x in package_imports]
    package_list_string = ', '.join(package_list)

    sql_statements = []

    table_2_df = []
    table_2_df_param_list = []
    for param in function.parameters:
        if param.type == 'DataFrame':
            table_2_df.append(str(param.pos))
            table_2_df_param_list.append(f"'{param.name}'")

    param_list_string = ', '.join(
        [param.name for param in function.parameters])
    table_2_df_param_list_string = ', '.join(table_2_df_param_list)

    sql_statements.append(
        f'put file://{file_path} @{stage}/{function.name}/{version}')
    sql_statements.append(f"""create or replace procedure {function.name}({function.sql_param_list()})
    returns {function.returns.sql_type()}
    language python
    runtime_version = '3.8'
    packages = ({package_list_string})
    imports = ({import_list_string})
    handler = 'procedure_handler'
AS
$$
from {function.module_name} import {function.name}
from modelstar import SNOWFLAKE_SESSION_STATE, modelstar_table_df, get_kwargs
from snowflake.snowpark.session import Session

def procedure_handler(session: Session, {param_list_string}):
    SNOWFLAKE_SESSION_STATE.session = session
    
    kwargs = get_kwargs()

    arg_vals = []
    for param_name, param_val in kwargs.items():
        if not isinstance(param_val, Session):
            if param_name in [{table_2_df_param_list_string}]:
                arg_vals.append(modelstar_table_df(param_val))
            else:
                arg_vals.append(param_val)

    return {function.name}(*arg_vals)
$$;""")

    return sql_statements


def put_file_from_local(config: SnowflakeConfig, file_path: str, stage_path: str = None):

    # TODO add threads to this to make this faster.
    sql_statements = []
    if stage_path is not None:
        sql_statements.append(
            f'PUT file://{file_path} @{config.stage}/{stage_path}')
    else:
        sql_statements.append(f'PUT file://{file_path} @{config.stage}')

    return sql_statements


def clear_function_stage_files(config: SnowflakeConfig, function_name: str, version: str):

    sql_statements = []
    sql_statements.append(f'REMOVE @{config.stage}/{function_name}/{version}')

    return sql_statements


def create_table(config: SnowflakeConfig, table_info: TableInfo):

    sql_statements = []
    sql_statements.append(f'CREATE OR REPLACE TABLE {table_info.name} (')
    for idx, column in enumerate(table_info.columns):
        if idx == (len(table_info.columns)-1):
            sql_statements.append(f'{column.name} {column.snow_type}')
        else:
            sql_statements.append(f'{column.name} {column.snow_type},')

    sql_statements.append(f');')

    return [' '.join(sql_statements)]


def create_file_format(config: SnowflakeConfig, file_format: FileFormat):

    sql_statements = []
    sql_statements.append(
        f"CREATE OR REPLACE FILE FORMAT {file_format.format_name} type = '{file_format.format_type}' field_delimiter = '{file_format.delimiter}' SKIP_HEADER = {file_format.skip_header};")

    return sql_statements


def copy_file_into_table(config: SnowflakeConfig, table_info: TableInfo, file_stage_path: str, file_format: FileFormat):

    sql_statements = []
    sql_statements.append(
        f'COPY INTO {table_info.name} from {file_stage_path} file_format={file_format.format_name};')

    return sql_statements


'''
TODO

Parse
- function file to get its dependencies and files

Check for: 
- database if it exists
- schema if it exists
- stage if it exists
- permission to write to it if it exists
- check if the function or the files with the names exists

https://github.com/snowflakedb/snowpark-python/blob/1ee21420b704e1ad595257b95365567fa864fddc/src/snowflake/snowpark/udf.py#L96
'''
