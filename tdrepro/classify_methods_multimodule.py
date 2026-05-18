#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def method_owner(line: str) -> str:
    line = line.strip()
    if not line or "." not in line:
        return ""
    return line.split(".", 1)[0]

def load_all_project_classes(project_root: str):
    root = Path(project_root)
    project_classes = set()

    for class_dir in root.rglob("target/classes"):
        for cls in class_dir.rglob("*.class"):
            rel = cls.relative_to(class_dir)
            owner = str(rel).replace(os.sep, "/").replace(".class", "")
            project_classes.add(owner)

    for class_dir in root.rglob("target/test-classes"):
        for cls in class_dir.rglob("*.class"):
            rel = cls.relative_to(class_dir)
            owner = str(rel).replace(os.sep, "/").replace(".class", "")
            project_classes.add(owner)

    return project_classes

def classify_methods(input_file, project_classes):
    project_methods = []
    library_methods = []

    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            raw = line.strip()
            if not raw:
                continue

            owner = method_owner(raw)

            if owner in project_classes:
                project_methods.append(raw)
            else:
                library_methods.append(raw)

    return project_methods, library_methods

def main():
    if len(sys.argv) != 3:
        print("Usage: python classify_methods_multimodule.py <project_root> <executed_methods_dir>")
        sys.exit(1)

    project_root = sys.argv[1]
    input_file = Path(sys.argv[2])

    project_classes = load_all_project_classes(project_root)
    print(f"Loaded project classes: {len(project_classes)}")
    project_methods, library_methods = classify_methods(input_file, project_classes)

    out_dir = input_file.parent / "classified"
    out_dir.mkdir(parents=True, exist_ok=True)
    project_out = out_dir / f"{input_file.stem}-project-methods.txt"
    library_out = out_dir / f"{input_file.stem}-library-methods.txt"

    project_out.write_text("\n".join(project_methods) + "\n", encoding="utf-8")
    library_out.write_text("\n".join(library_methods) + "\n", encoding="utf-8")

    print(f"Processed: {input_file.name}")
    print(f"Project methods: {len(project_methods)}")
    print(f"Library methods: {len(library_methods)}")
    print(f"Saved to: {out_dir}")


if __name__ == "__main__":
    main()
