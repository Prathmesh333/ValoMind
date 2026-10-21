"""Render embedded Python sources without a single line of escaped file contents."""


def source_dictionary(name, sources):
    """Keep source bytes intact while displaying normal line breaks in notebook cells."""
    entries = [f"{name} = {{\n"]
    for filename, source in sorted(sources.items()):
        # Raw multiline literals preserve regex escapes and original file contents.
        # Fall back to repr for sources that contain both possible delimiters.
        delimiter = next((quote for quote in ("'''", '"""') if quote not in source), None)
        if delimiter is None or source.endswith("\\"):
            literal = repr(source)
        else:
            literal = f"r{delimiter}{source}{delimiter}"
        entries.append(f"    {filename!r}: {literal},\n")
    entries.append("}\n")
    return "".join(entries)
