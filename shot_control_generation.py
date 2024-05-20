"""
This module produces shot gathers in segy format. Acoustic wave equations is used.
"""
from dask_cluster import DaskCluster


class ControlGetshot:
    """
    Class to generate the shot files based on the input coordinates or
    geometry parameters files
    """

    def generate_shot_files(self):
        "Fetches the input from files and starts to generate the shots"
        dc = DaskCluster()
        dc.gen_shots_cluster()
