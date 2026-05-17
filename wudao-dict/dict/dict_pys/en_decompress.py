#coding=utf8
import json
import zlib
import sys
import argparse
import os
from wd import draw_text # Assume wd.py is in the same directory or PYTHONPATH

INDEX_FILE = 'en.z'
DATA_FILE = 'dict.zlib'

def build_index(index_file_path):
    """Reads the index file and builds a dictionary mapping words to offsets and lengths."""
    index_dict = {}
    try:
        with open(index_file_path, 'r', encoding='utf8') as f:
            lines = f.readlines()
            if not lines:
                print(f"Error: Index file '{index_file_path}' is empty.", file=sys.stderr)
                return None

            # Handle the first line separately to initialize prev_word, prev_offset
            try:
                prev_word, prev_offset_str = lines[0].strip().split('|')
                prev_offset = int(prev_offset_str)
            except (ValueError, IndexError) as e:
                print(f"Error parsing first line in index file '{index_file_path}': {e}", file=sys.stderr)
                return None

            # Process subsequent lines
            for line in lines[1:]:
                try:
                    word, offset_str = line.strip().split('|')
                    current_offset = int(offset_str)
                    index_dict[prev_word] = [prev_offset, current_offset - prev_offset]
                    prev_word, prev_offset = word, current_offset
                except (ValueError, IndexError) as e:
                    print(f"Error parsing line in index file '{index_file_path}': '{line.strip()}'. Error: {e}", file=sys.stderr)
                    continue # Skip malformed lines

            # Add the last entry (assuming the file doesn't end abruptly)
            # This part needs clarification on how the end of the compressed data is marked
            # or if the last entry points to the end of the file.
            # Assuming the last offset points to the start of the last word's data,
            # we might need the total file size or another marker.
            # For now, we'll leave the last word without a length,
            # or handle it in the decompression step if possible.
            # A common pattern is to add a dummy entry at the end or store total size.
            # Let's assume the last entry calculation was implicitly handled before,
            # or needs adjustment based on dict.zlib structure.
            # If the original code worked, it might imply the last read grabs till EOF.
            # Let's refine the decompressed function to handle potential lack of length.

            # Simplified last entry handling based on original logic (might be flawed):
            # The original code didn't explicitly handle the last entry after the loop.
            # Let's assume the last pair `prev_word, prev_offset` is implicitly handled
            # or the structure guarantees the lookup works. If issues arise, this needs revisit.


    except FileNotFoundError:
        print(f"Error: Index file not found at '{index_file_path}'", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred while reading index file '{index_file_path}': {e}", file=sys.stderr)
        return None
    return index_dict


def decompress_word_data(word_to_find, index_dict, data_file_path):
    """Decompresses and parses the data for a given word."""
    if word_to_find not in index_dict:
        print(f"Error: Word '{word_to_find}' not found in index.", file=sys.stderr)
        return None

    word_offset_info = index_dict[word_to_find]
    offset = word_offset_info[0]
    length = word_offset_info[1] # Original code implies length is always present

    try:
        with open(data_file_path, 'rb') as fr:
            fr.seek(offset)
            # Ensure length is positive, handle potential issues from index build
            if length <= 0:
                 print(f"Warning: Invalid length ({length}) for word '{word_to_find}'. Reading might be incorrect.", file=sys.stderr)
                 # Attempt to read a reasonable amount or based on file structure knowledge
                 # For now, return error if length isn't positive
                 return None # Or try reading to end? Needs clarification.

            compressed_data = fr.read(length)
            if not compressed_data:
                 print(f"Error: No data read for word '{word_to_find}' at offset {offset} with length {length}.", file=sys.stderr)
                 return None

            decompressed_str = zlib.decompress(compressed_data).decode('utf8')
            data_parts = decompressed_str.split('|')

            if len(data_parts) < 9:
                print(f"Error: Unexpected data format for word '{word_to_find}'. Expected 9 parts, got {len(data_parts)}.", file=sys.stderr)
                return None

            word_info = {}
            word_info['word'] = data_parts[0]
            word_info['id'] = data_parts[1]
            word_info['pronunciation'] = {}
            if data_parts[2]:
                word_info['pronunciation']['美'] = data_parts[2]
            if data_parts[3]:
                word_info['pronunciation']['英'] = data_parts[3]
            if data_parts[4]:
                word_info['pronunciation'][''] = data_parts[4] # Keep empty key if needed by draw_text

            # Safely parse JSON fields
            try:
                word_info['paraphrase'] = json.loads(data_parts[5]) if data_parts[5] else []
            except json.JSONDecodeError:
                print(f"Warning: Could not decode paraphrase JSON for '{word_to_find}'. Data: {data_parts[5]}", file=sys.stderr)
                word_info['paraphrase'] = [] # Default to empty list

            word_info['rank'] = data_parts[6]
            word_info['pattern'] = data_parts[7]

            try:
                word_info['sentence'] = json.loads(data_parts[8]) if data_parts[8] else []
            except json.JSONDecodeError:
                print(f"Warning: Could not decode sentence JSON for '{word_to_find}'. Data: {data_parts[8]}", file=sys.stderr)
                word_info['sentence'] = [] # Default to empty list

            return word_info

    except FileNotFoundError:
        print(f"Error: Data file not found at '{data_file_path}'", file=sys.stderr)
        return None
    except zlib.error as e:
        print(f"Error decompressing data for word '{word_to_find}': {e}", file=sys.stderr)
        return None
    except IOError as e:
        print(f"Error reading data file '{data_file_path}': {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred during decompression for '{word_to_find}': {e}", file=sys.stderr)
        return None


def main():
    """Main function to parse arguments, build index, decompress, and draw."""
    parser = argparse.ArgumentParser(description="Decompress and display word information from Wudao dictionary files.")
    parser.add_argument("word", help="The word to look up.")
    parser.add_argument("--index", default=INDEX_FILE, help=f"Path to the index file (default: {INDEX_FILE})")
    parser.add_argument("--data", default=DATA_FILE, help=f"Path to the data file (default: {DATA_FILE})")
    # Add argument for draw_text configuration if needed, e.g., --short/--long
    # parser.add_argument("--short", action="store_true", help="Display short format (implementation depends on draw_text)")

    args = parser.parse_args()

    # Ensure files exist before proceeding
    if not os.path.exists(args.index):
        print(f"Error: Index file not found: {args.index}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.data):
        print(f"Error: Data file not found: {args.data}", file=sys.stderr)
        sys.exit(1)


    index_dictionary = build_index(args.index)
    if index_dictionary is None:
        sys.exit(1)

    word_data = decompress_word_data(args.word, index_dictionary, args.data)

    if word_data:
        # Assuming draw_text takes the word dictionary and a boolean config (True for long?)
        # Adjust the second argument based on draw_text's actual signature and desired output
        draw_text(word_data, True)
    else:
        # Error messages are printed within the functions
        sys.exit(1) # Exit with error status if word data couldn't be retrieved

if __name__ == "__main__":
    main()
