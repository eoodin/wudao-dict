#!/usr/bin/python3
# -*- coding: utf-8 -*-

import zlib
import json
import sys
import os
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
DEFAULT_INPUT_FILE = "c.txt" # Assuming this contains the list of words
DEFAULT_OUTPUT_FILE = "dict.zlib"
DEFAULT_INDEX_FILE = "dict.zlib.index" # Assuming this is the intended index file name
DEFAULT_CACHE_DIR = "cache"
COMPRESSION_LEVEL = 6 # Default zlib compression level

def process_word(word, cache_dir):
    """Loads, processes, and prepares data for a single word from its cache file."""
    dcache_path = os.path.join(cache_dir, word)
    if not os.path.exists(dcache_path):
        logging.warning(f"Cache file not found for '{word}' at '{dcache_path}'")
        return None, None # Return None for both word_data and raw_word

    try:
        with open(dcache_path, 'r', encoding='utf-8') as f:
            word_data = json.load(f)

        # Extract necessary fields for the compressed format
        # Ensure all expected keys exist, provide defaults if necessary
        word_test = word_data.get('word', word) # Use cached word, fallback to input word
        raw_word = word_data.get('raw_word', word) # Store the original word form if available
        wid = word_data.get('id', '') # Assuming 'id' might exist in cache
        us_phonetic = word_data.get('pronunciation', {}).get('美', '')
        uk_phonetic = word_data.get('pronunciation', {}).get('英', '')
        unknown_phonetic = word_data.get('pronunciation', {}).get('', '') # Handle empty key if used
        paraphrase = json.dumps(word_data.get('paraphrase', []), ensure_ascii=False, separators=(',', ':'))
        rank = word_data.get('rank', '')
        pattern = word_data.get('pattern', '')
        sentence = json.dumps(word_data.get('sentence', []), ensure_ascii=False, separators=(',', ':'))

        # Format the line for compression
        afline = f"{word_test}|{wid}|{us_phonetic}|{uk_phonetic}|{unknown_phonetic}|{paraphrase}|{rank}|{pattern}|{sentence}"
        return afline, raw_word

    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from {dcache_path}: {e}")
        return None, None
    except Exception as e:
        logging.error(f"Error processing file {dcache_path}: {e}")
        return None, None

def compress_dictionary(input_file, output_file, index_file, cache_dir):
    """Reads words from input_file, processes cache, compresses, and writes output files."""
    word_list = []
    # Read word list
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            word_list = [x.strip() for x in f if x.strip()] # Read non-empty lines
        if not word_list:
            logging.error(f"Input file '{input_file}' is empty or contains no valid words.")
            return False
    except FileNotFoundError:
        logging.error(f"Input file '{input_file}' not found.")
        return False
    except Exception as e:
        logging.error(f"Error reading input file '{input_file}': {e}")
        return False

    # Process words and prepare for writing
    processed_data = []
    total_words = len(word_list)
    processed_count = 0
    skipped_count = 0

    for i, word in enumerate(word_list):
        afline, raw_word_for_index = process_word(word, cache_dir)
        if afline and raw_word_for_index:
            try:
                acf_line = zlib.compress(afline.encode('utf8'), COMPRESSION_LEVEL)
                processed_data.append({'index_word': raw_word_for_index, 'data': acf_line})
                processed_count += 1
            except zlib.error as e:
                logging.error(f"Error compressing data for word '{word}': {e}")
                skipped_count += 1
            except Exception as e:
                 logging.error(f"Unexpected error during compression for word '{word}': {e}")
                 skipped_count += 1
        else:
            skipped_count += 1

        if (i + 1) % 100 == 0 or (i + 1) == total_words: # Log progress periodically
             logging.info(f"Processed {i + 1}/{total_words} words...")


    if not processed_data:
        logging.error("No words were successfully processed. Aborting.")
        return False

    # Write compressed data and index
    try:
        current_offset = 0
        with open(output_file, 'wb') as fw, open(index_file, 'w', encoding='utf-8') as fi:
            for item in processed_data:
                fi.write(f"{item['index_word']}|{current_offset}\n")
                data_len = fw.write(item['data'])
                current_offset += data_len
            # Add final entry to index to mark the end? Or is the length calculation sufficient?
            # The original decompress logic relies on offset differences.
            # Add a final marker line for the last word's end offset.
            fi.write(f"__EOF__|{current_offset}\n") # Use a special marker

        logging.info(f"Successfully compressed {processed_count} words.")
        if skipped_count > 0:
            logging.warning(f"Skipped {skipped_count} words due to errors.")
        logging.info(f"Output data file: {output_file}")
        logging.info(f"Output index file: {index_file}")
        return True

    except IOError as e:
        logging.error(f"Error writing output file(s) ('{output_file}', '{index_file}'): {e}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred during writing: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compress word data from cache files into a ZLIB compressed dictionary and index.")
    parser.add_argument("-i", "--input", default=DEFAULT_INPUT_FILE,
                        help=f"Path to the input file containing the list of words (default: {DEFAULT_INPUT_FILE})")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT_FILE,
                        help=f"Path to the output compressed data file (default: {DEFAULT_OUTPUT_FILE})")
    parser.add_argument("-x", "--index", default=DEFAULT_INDEX_FILE,
                        help=f"Path to the output index file (default: {DEFAULT_INDEX_FILE})")
    parser.add_argument("-c", "--cache", default=DEFAULT_CACHE_DIR,
                        help=f"Path to the cache directory containing JSON files (default: {DEFAULT_CACHE_DIR})")

    args = parser.parse_args()

    if not os.path.isdir(args.cache):
        logging.error(f"Cache directory '{args.cache}' not found or is not a directory.")
        sys.exit(1)

    if compress_dictionary(args.input, args.output, args.index, args.cache):
        logging.info("Compression process completed successfully.")
        sys.exit(0)
    else:
        logging.error("Compression process failed.")
        sys.exit(1)

# Removed the unused draw_text function
# def draw_text(word, fw, fi, wid):
#     # ... (original function content was here)

