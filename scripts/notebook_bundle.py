"""Emit notebook file-writing cells with readable Python source."""


def source_cells(cell, sources, directory):
    """Write each module in an IPython cell, retaining package-relative imports."""
    for filename, source in sorted(sources.items()):
        cell(
            "markdown",
            f"### Worker file: `{filename}`\nRun this cell to write the file; imports load it during initialization.\n",
        )
        cell("code", f"%%writefile {directory}/{filename}\n" + source)
