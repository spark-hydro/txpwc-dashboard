import os

def create_pcpfile_cio(station_ids, out_folder):
    """
    Generate pcpfile.cio listing all precipitation stations
    """
    path = os.path.join(out_folder, "pcpfile.cio")

    with open(path, "w") as f:
        f.write(f"{len(station_ids)}\n")
        for sid in station_ids:
            f.write(f"{sid}.pcp\n")

    return path


def create_tmpfile_cio(station_ids, out_folder):
    """
    Generate tmpfile.cio listing all temperature stations
    """
    path = os.path.join(out_folder, "tmpfile.cio")

    with open(path, "w") as f:
        f.write(f"{len(station_ids)}\n")
        for sid in station_ids:
            f.write(f"{sid}.tmp\n")

    return path
