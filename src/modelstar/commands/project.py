import os
from shutil import copytree
from modelstar.templates import TEMPLATES_PATH
import click


def initialize_project(project_name: str):
    current_working_directory = os.getcwd()
    # current_folder_name = os.path.basename(current_working_directory)
    base_template_path = os.path.join(TEMPLATES_PATH, 'snowflake_project')

    if project_name != '.':
        project_folder_path = os.path.join(
            current_working_directory, project_name)
        try:
            destination = copytree(base_template_path, project_folder_path)
        except FileExistsError as e:
            click.echo(f"Project not initialized.\n\nFileExitsError: {e}")
    else:
        # If the project_name is = ., create the files inside this folder.
        # Check if the files and folders inside this folder don't have the names we are using.
        try:
            destination = copytree(
                base_template_path, current_working_directory)
        except FileExistsError as e:
            click.echo(
                f"Project not initialized. There are files in the current folder that conflict with the project initialization.\n\nFileExitsError: {e}")

    return destination
