#!/usr/bin/env python3
#
# Merge exported session buddy *.txt files (or any files with one url per line)
#
# author: acegene <acegene22@gmail.com>
# todos
#   * check encoding

import argparse
import os
import re


## Use regex to remove the first instance of "uri=" and everything before it
def remove_uri_prefix(url):
    return re.sub(r".*?uri=", "", url, 1)


## Use regex to replace "https://www." with "https://"
def remove_www(url):
    return re.sub(r"https://www\.", "https://", url)


def merge_and_sort_text_files(dir_session_files, path_file_out):
    # Get a list of all text files in the specified directory
    text_files = [f for f in os.listdir(dir_session_files) if f.endswith(".txt")]

    # Check if there are any text files in the directory
    if not text_files:
        print("No text files found in the specified directory.")
        return

    # Initialize an empty list to store lines from all files
    unique_lines = set()

    # Read lines from each text file and append them to the list
    for file_name in text_files:
        file_path = os.path.join(dir_session_files, file_name)
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
            lines_cleaned = [remove_www(remove_uri_prefix(line)) for line in lines if line.strip()]
            unique_lines.update(lines_cleaned)

    # Sort all lines alphabetically
    soreted_lines = sorted(list(unique_lines))

    # Write the sorted lines to the output file
    with open(path_file_out, "w", encoding="utf-8") as output_file:
        output_file.writelines(soreted_lines)

    print(f"INFO: wrote merged output to '{path_file_out}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge and sort text files in a directory.")
    parser.add_argument("--dir-session-files", "-i", required=True, help="Path to the directory containing text files.")
    parser.add_argument("--path-file-out", "-o", required=True, help="Path to the output file.")

    args = parser.parse_args()

    merge_and_sort_text_files(args.dir_session_files, args.path_file_out)
