import os
import openai
import subprocess
from collections import defaultdict
from pygments.lexers import get_lexer_for_filename, guess_lexer_for_filename, ClassNotFound

openai.api_key = "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"

def search_readme():

    readme_files = [f for f in os.listdir() if f.lower().startswith("readme")]

    if readme_files:

        with open(readme_files[0], "r", encoding="utf-8") as f:

            readme_contents = f.read()

    else:

        readme_contents = ""

    return readme_contents.strip()

def scan_files():
    file_tree = defaultdict(list)
    build_files = []

    for root, dirs, files in os.walk("."):
        for file in files:
            file_tree[root].append(file)
            if file.lower().endswith((".md", ".rst", ".yml", ".yaml", ".json", ".sh", ".bat", ".ps1")):
                build_files.append(os.path.join(root, file))

    return file_tree, build_files

def detect_os(build_files):

    detected_os = set()

    for file in build_files:

        if file.lower().endswith(".sh") or file.lower().endswith(".ps1"):

            detected_os.add("unix")

        if file.lower().endswith(".bat"):

            detected_os.add("windows")

    return detected_os

def detect_languages(build_files):

    detected_languages = set()

    for file in build_files:

        _, ext = os.path.splitext(file)

        ext = ext.lower()

        if ext in {".py", ".ipynb"}:

            detected_languages.add("python")

        elif ext in {".js", ".ts"}:

            detected_languages.add("javascript")

        elif ext in {".java"}:

            detected_languages.add("java")

        elif ext in {".cpp", ".c", ".h"}:

            detected_languages.add("c++")

    return detected_languages

def build_instructions_prompt(detected_os, detected_languages, readme_contents, build_files_str, file_tree_str):

    os_list = ", ".join(detected_os)

    languages_list = ", ".join(detected_languages)

    prompt = f"A GitHub repository contains the following README content:\n\n{readme_contents}\n\nThe repository has files for the following operating systems: {os_list}\n\nThe repository uses the following programming languages: {languages_list}\n\nThe build-related files in the repository are:\n\n{build_files_str}\n\nThe file tree of the repository is:\n\n{file_tree_str}\n\nProvide build instructions (in a YAML format) to build the project:"

    return prompt

def get_build_instructions(prompt):

    response = openai.Completion.create(

        engine="text-davinci-002",

        prompt=prompt,

        max_tokens=150,

        n=1,

        stop=None,

        temperature=0.5,

    )

    build_commands = response.choices[0].text.strip()

    return build_commands

def refine_build_instructions(build_commands, max_iterations=3):

    for i in range(max_iterations):

        prompt = f"Refine the following build commands to improve their success rate:\n\n{build_commands}\n\nRefined build commands:"

        response = openai.Completion.create(

            engine="text-davinci-002",

            prompt=prompt,

            max_tokens=150,

            n=1,

            stop=None,

            temperature=0.5,

        )

        build_commands = response.choices[0].text.strip()

    return build_commands

def create_workflow_file(build_commands):

    with open(".github/workflows/generated_build.yml", "w", encoding="utf-8") as f:

        f.write("name: Generated Build\n\n")

        f.write("on:\n  push:\n    branches:\n      - main\n  pull_request:\n    branches:\n      - main\n\n")

        f.write("jobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n    - name: Checkout code\n      uses: actions/checkout@v2\n\n")

        f.write(build_commands)

def main():

    readme_contents = search_readme()

    file_tree, build_files = scan_files()

    detected_os = detect_os(build_files)

    detected_languages = detect_languages(build_files)

    file_tree_str = "\n".join([f"{root}: {", ".join(files)}" for root, files in file_tree.items()])

    build_files_str = "\n".join(build_files)

    prompt = build_instructions_prompt(detected_os, detected_languages, readme_contents, build_files_str, file_tree_str)

    build_commands = get_build_instructions(prompt)

    refined_build_commands = refine_build_instructions(build_commands)

    create_workflow_file(refined_build_commands)

    subprocess.run("git config --global user.name 'GitHub Actions'", shell=True, check=True)

    subprocess.run("git config --global user.email 'actions@github.com'", shell=True, check=True)

    subprocess.run("git add .github/workflows/generated_build.yml", shell=True, check=True)

    subprocess.run("git commit -m 'Add generated build workflow'", shell=True, check=True)

    subprocess.run("git push", shell=True, check=True)

if __name__ == "__main__":
    main()
