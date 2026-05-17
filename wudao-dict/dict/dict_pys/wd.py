# -*- coding: utf-8 -*-
import argparse
import sys
import os
# Assuming WudaoOnline and potentially local dictionary access modules are importable
# If this script is run standalone, these imports might need adjustment
# from ...src import WudaoOnline # Example relative import if part of a package
# from . import en_decompress, zh_decompress # Example relative import

# Define color patterns (consider moving to a config or constants file)
RED_PATTERN = '\033[31m%s\033[0m'
GREEN_PATTERN = '\033[32m%s\033[0m'
BLUE_PATTERN = '\033[34m%s\033[0m'
PEP_PATTERN = '\033[36m%s\033[0m'
BROWN_PATTERN = '\033[33m%s\033[0m'

def draw_text(word_info, show_sentence=True):
    """Prints formatted English word information to the console."""
    if not word_info:
        print("Error: No word information to display.", file=sys.stderr)
        return

    # Word
    print(RED_PATTERN % word_info.get('word', 'N/A'))

    # Pronunciation
    pronunciation = word_info.get('pronunciation', {})
    pron_parts = []
    if pronunciation.get('美'):
        pron_parts.append(f"美[{pronunciation['美']}]")
    if pronunciation.get('英'):
        pron_parts.append(f"英[{pronunciation['英']}]")
    if pron_parts:
        print(PEP_PATTERN % ' '.join(pron_parts))

    # Paraphrase
    paraphrase = word_info.get('paraphrase', [])
    if paraphrase:
        for item in paraphrase:
            print(BLUE_PATTERN % item)

    # Rank & Pattern
    rank = word_info.get('rank', '')
    pattern = word_info.get('pattern', '')
    if rank or pattern:
        print(BROWN_PATTERN % f"{rank} {pattern}".strip())

    # Sentence examples
    if show_sentence:
        sentences = word_info.get('sentence', [])
        if sentences:
            print('\n例句:')
            for i, sentence_pair in enumerate(sentences, 1):
                if len(sentence_pair) == 2:
                    print(f"{i}. {sentence_pair[0]}")
                    print(f"   {sentence_pair[1]}")

def draw_zh_text(word_info, show_details=True):
    """Prints formatted Chinese word information to the console."""
    if not word_info:
        print("Error: No word information to display.", file=sys.stderr)
        return

    # Word
    print(RED_PATTERN % word_info.get('word', 'N/A'))

    # Pronunciation (Pinyin)
    pronunciation = word_info.get('pronunciation')
    if pronunciation:
        print(PEP_PATTERN % f"[{pronunciation}]")

    # Paraphrase (Basic English translation)
    paraphrase = word_info.get('paraphrase', [])
    if paraphrase:
        print(f"基本释义:")
        for item in paraphrase:
            item = item.replace('  ;  ', ', ') # Clean up separators
            print(BLUE_PATTERN % item)

    # Detailed Description
    if show_details:
        descriptions = word_info.get('desc', [])
        if descriptions:
            print('\n详细释义:')
            for count, desc_item in enumerate(descriptions, 1):
                if not desc_item or not isinstance(desc_item, list) or len(desc_item) < 1:
                    continue

                title = desc_item[0].replace(';', ',') # Clean title
                print(f"{count}. {GREEN_PATTERN % title}")

                if len(desc_item) == 2 and isinstance(desc_item[1], list):
                    examples = desc_item[1]
                    for sub_count, example_pair in enumerate(examples):
                         if len(example_pair) == 2:
                             definition = example_pair[0].strip().replace(';', '')
                             example_sentence = example_pair[1].strip()
                             # Indent examples for clarity
                             print(f"    - {definition}")
                             if example_sentence:
                                 print(f"      {BROWN_PATTERN % example_sentence}")
                         elif len(example_pair) == 1: # Handle cases with only definition or example
                             print(f"    - {example_pair[0].strip().replace(';', '')}")

        # Sentence examples (Chinese-English pairs)
        sentences = word_info.get('sentence', [])
        if sentences:
            print('\n例句:')
            for i, sentence_pair in enumerate(sentences, 1):
                if len(sentence_pair) == 2:
                    print(f"{i}. {sentence_pair[0]}") # Chinese sentence
                    print(f"   {sentence_pair[1]}") # English translation

def main():
    parser = argparse.ArgumentParser(description='Wudao Dictionary Command Line Tool')
    parser.add_argument('word', nargs='?', help='The word or phrase to look up.')
    parser.add_argument('-s', '--short', action='store_true', help='Show short description (no sentences/details).')
    # Add other arguments as needed, e.g., -i for interactive, -n for notebook, etc.
    # These would require integrating logic from WudaoCommand.py

    args = parser.parse_args()

    if not args.word:
        parser.print_help()
        sys.exit(0)

    word_to_lookup = args.word
    show_full = not args.short

    # Determine if the word is Chinese or English (simple check)
    # A more robust check might be needed
    is_zh = any('\u4e00' <= char <= '\u9fff' for char in word_to_lookup)

    # Placeholder for fetching logic: Should integrate local dictionary lookup first,
    # then fallback to online search using WudaoOnline functions.
    word_info = None
    print(f"Looking up '{word_to_lookup}'...")

    # Example: Simplified logic (replace with actual lookup)
    try:
        if is_zh:
            # 1. Try local zh_decompress
            # word_info = zh_decompress.decompress_word_data(word_to_lookup, ...)
            # if not word_info:
            #    print("Not found locally, searching online...")
            #    from src import WudaoOnline # Adjust import path
            #    word_info = WudaoOnline.get_zh_text(word_to_lookup)
            pass # Replace with actual call
        else:
            # 1. Try local en_decompress
            # word_info = en_decompress.decompress_word_data(word_to_lookup, ...)
            # if not word_info:
            #    print("Not found locally, searching online...")
            #    from src import WudaoOnline # Adjust import path
            #    word_info = WudaoOnline.get_text(word_to_lookup)
            pass # Replace with actual call

        # Dummy data for demonstration if lookup not implemented yet
        if not word_info:
             if is_zh:
                 print("(Using dummy data for Chinese)")
                 word_info = {'word': word_to_lookup, 'pronunciation': 'pinyin', 'paraphrase': ['基本释义1', '基本释义2'], 'desc': [['详细释义标题1', [['定义1', '例句1'], ['定义2', '例句2']]], ['标题2', []]], 'sentence': [['中文例句1', 'English Sentence 1']]} 
             else:
                 print("(Using dummy data for English)")
                 word_info = {'word': word_to_lookup, 'pronunciation': {'美': 'US', '英': 'UK'}, 'paraphrase': ['basic meaning 1', 'basic meaning 2'], 'rank': 'CET4', 'pattern': '*', 'sentence': [['English Sentence 1', '中文例句1'], ['Sentence 2', '例句2']]} 

    except ImportError as e:
        print(f"Error: Could not import necessary modules. {e}", file=sys.stderr)
        print("Please ensure the script is run correctly within the project structure.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred during lookup: {e}", file=sys.stderr)
        sys.exit(1)

    # Display the result
    if word_info:
        if is_zh:
            draw_zh_text(word_info, show_full)
        else:
            draw_text(word_info, show_full)
    else:
        print(f"Could not find information for '{word_to_lookup}'.")

if __name__ == '__main__':
    main()

