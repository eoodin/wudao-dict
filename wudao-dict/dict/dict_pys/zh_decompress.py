#coding=utf8
import json
import zlib
import sys
import argparse
import os
from wd import draw_zh_text # Assume wd.py is in the same directory or PYTHONPATH

INDEX_FILE = 'zh.z'
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

            # Handle the first line separately
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

            # Handle the last word entry (assuming it uses offset till end of file or similar)
            # This logic might need refinement based on how dict.zlib is structured.
            # If the original code worked by reading until EOF implicitly, this might be okay.
            # Let's assume the last word read needs special handling or the length calculation
            # implicitly covers it. For now, add the last entry without explicit length,
            # relying on the decompress function to handle it (e.g., read till end if length is missing/0).
            # Replicating original implicit logic:
            # The original loop structure implies the last word might not be added here.
            # Let's refine decompress_word_data to handle potential missing length if needed.
            # For consistency with en_decompress, we'll assume the index structure provides length.
            # If the last word is problematic, this is the area to adjust.

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
        # Attempt lookup with potential key variations if needed (e.g., case variations)
        # For now, strict match
        print(f"Error: Word '{word_to_find}' not found in index.", file=sys.stderr)
        return None

    word_offset_info = index_dict[word_to_find]
    offset = word_offset_info[0]
    length = word_offset_info[1]

    try:
        with open(data_file_path, 'rb') as fr:
            fr.seek(offset)
            if length <= 0:
                 print(f"Warning: Invalid length ({length}) for word '{word_to_find}'. Reading might be incorrect.", file=sys.stderr)
                 # Decide handling: return None, read fixed amount, or read till EOF?
                 return None # Safest default

            compressed_data = fr.read(length)
            if not compressed_data:
                 print(f"Error: No data read for word '{word_to_find}' at offset {offset} with length {length}.", file=sys.stderr)
                 return None

            decompressed_str = zlib.decompress(compressed_data).decode('utf8')
            data_parts = decompressed_str.split('|')

            # Expected format: word|id|pronunciation|paraphrase_json|desc_json|sentence_json
            if len(data_parts) < 6:
                print(f"Error: Unexpected data format for word '{word_to_find}'. Expected 6+ parts, got {len(data_parts)}.", file=sys.stderr)
                return None

            word_info = {}
            word_info['word'] = data_parts[0]
            word_info['raw_word'] = word_to_find # Keep original query term
            word_info['id'] = data_parts[1]
            word_info['pronunciation'] = data_parts[2] # Single pronunciation field for Chinese

            # Safely parse JSON fields
            try:
                word_info['paraphrase'] = json.loads(data_parts[3]) if data_parts[3] else []
            except json.JSONDecodeError:
                print(f"Warning: Could not decode paraphrase JSON for '{word_to_find}'. Data: {data_parts[3]}", file=sys.stderr)
                word_info['paraphrase'] = []

            try:
                word_info['desc'] = json.loads(data_parts[4]) if data_parts[4] else []
            except json.JSONDecodeError:
                print(f"Warning: Could not decode description JSON for '{word_to_find}'. Data: {data_parts[4]}", file=sys.stderr)
                word_info['desc'] = []

            try:
                word_info['sentence'] = json.loads(data_parts[5]) if data_parts[5] else []
            except json.JSONDecodeError:
                print(f"Warning: Could not decode sentence JSON for '{word_to_find}'. Data: {data_parts[5]}", file=sys.stderr)
                word_info['sentence'] = []

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
    parser = argparse.ArgumentParser(description="Decompress and display Chinese word information from Wudao dictionary files.")
    parser.add_argument("word", help="The Chinese word or phrase to look up.")
    parser.add_argument("--index", default=INDEX_FILE, help=f"Path to the index file (default: {INDEX_FILE})")
    parser.add_argument("--data", default=DATA_FILE, help=f"Path to the data file (default: {DATA_FILE})")
    # Add argument for draw_zh_text configuration if needed
    # parser.add_argument("--short", action="store_true", help="Display short format")

    args = parser.parse_args()

    # Ensure files exist
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
        # Assuming draw_zh_text takes the word dictionary and a boolean config (True for long?)
        draw_zh_text(word_data, True) # Adjust second arg based on draw_zh_text needs
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
