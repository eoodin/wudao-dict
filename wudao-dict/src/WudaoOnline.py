# -*- coding: utf-8 -*-

import bs4
from .soupselect import select as ss
from urllib.request import urlopen, Request
from urllib.parse import quote
from urllib.error import URLError, HTTPError
import logging # Use logging for errors/warnings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define a User-Agent to mimic a browser
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
REQUEST_TIMEOUT = 10 # seconds

def get_html(url):
    """Fetches HTML content from a URL with timeout and error handling."""
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            # Check if the request was successful
            if response.status == 200:
                # Try decoding with utf-8 first, fallback to autodetection or other encodings if needed
                try:
                    return response.read().decode('utf-8')
                except UnicodeDecodeError:
                    logging.warning(f"Could not decode {url} with UTF-8, trying with detected encoding.")
                    # Fallback or re-read with detected encoding if possible
                    # For simplicity, returning None here, but more robust handling might be needed
                    return None # Or try response.info().get_content_charset()
            else:
                logging.error(f"HTTP Error {response.status} for URL: {url}")
                return None
    except HTTPError as e:
        logging.error(f"HTTP Error fetching {url}: {e.code} {e.reason}")
        return None
    except URLError as e:
        logging.error(f"URL Error fetching {url}: {e.reason}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error fetching {url}: {e}")
        return None

def multi_space_to_single(text):
    """Replaces multiple spaces with a single space."""
    if text:
        return ' '.join(text.split())
    return text

def _parse_with_lxml(html_content):
    """Attempts to parse HTML using lxml, falls back to html.parser."""
    try:
        return bs4.BeautifulSoup(html_content, 'lxml')
    except bs4.FeatureNotFound:
        logging.warning("lxml not found, falling back to html.parser. Install lxml for potentially faster parsing.")
        return bs4.BeautifulSoup(html_content, 'html.parser')
    except Exception as e:
        logging.error(f"Error parsing HTML: {e}")
        return None

# get word info online
def get_text(word):
    """Fetches and parses English word information from Youdao."""
    url = f"http://dict.youdao.com/search?q={quote(word)}"
    html = get_html(url)
    if not html:
        return None

    soup = _parse_with_lxml(html)
    if not soup:
        return None

    dic = {'word': word, 'pronunciation': {}, 'paraphrase': [], 'rank': '', 'pattern': '', 'sentence': []}

    # Pronunciation (UK and US)
    ph_elements = ss(soup, '.baav .phonetic') # More specific selector
    if len(ph_elements) > 0:
        dic['pronunciation']['美'] = ph_elements[0].text.strip()
    if len(ph_elements) > 1:
        dic['pronunciation']['英'] = ph_elements[1].text.strip()

    # Paraphrase (Basic meaning)
    collins_section = soup.find('div', {'id': 'collinsResult'}) # Look within Collins section first
    if collins_section:
        paraphrase_items = ss(collins_section, '.collinsMajorTrans p .text')
        if paraphrase_items: # Found in Collins
             dic['paraphrase'] = [item.text.strip() for item in paraphrase_items]
        else: # Fallback to basic definition if Collins fails
             basic_trans = ss(soup, '#phrsListTab .trans-container ul li')
             dic['paraphrase'] = [li.text.strip() for li in basic_trans]
    else: # Fallback if no Collins section
        basic_trans = ss(soup, '#phrsListTab .trans-container ul li')
        dic['paraphrase'] = [li.text.strip() for li in basic_trans]

    # Rank and Pattern (e.g., ZK / GK / CET4 / CET6 etc.)
    rank_pattern = ss(soup, '#phrsListTab .rank')
    if rank_pattern:
        dic['rank'] = rank_pattern[0].text.strip()
    pattern_tag = ss(soup, '#phrsListTab .pattern a') # Assuming pattern is linked
    if pattern_tag:
        dic['pattern'] = pattern_tag[0].text.strip()
    elif not dic['rank']: # Sometimes pattern is in .pattern span directly
        pattern_span = ss(soup, '#phrsListTab .pattern')
        if pattern_span:
             dic['pattern'] = pattern_span[0].text.strip()


    # Sentences (Example sentences)
    sentence_pairs = ss(soup, '#bilingual .sentence-pair')
    for pair in sentence_pairs[:5]: # Limit to first 5 sentences
        en_s = pair.find('p', recursive=False) # Find direct child p for English
        zh_s = pair.find_all('p')[1] if len(pair.find_all('p')) > 1 else None # Second p for Chinese

        if en_s and zh_s:
            en_text = ''.join(en_s.stripped_strings)
            zh_text = ''.join(zh_s.stripped_strings)
            dic['sentence'].append([en_text, zh_text])

    # Check if essential info is missing
    if not dic['paraphrase']:
        logging.warning(f"No paraphrase found for '{word}' on Youdao.")
        # Optionally return None or the partial dict based on requirements
        # return None

    return dic

def get_zh_text(word):
    """Fetches and parses Chinese word information from Youdao."""
    url = f"http://dict.youdao.com/search?q={quote(word)}"
    html = get_html(url)
    if not html:
        return None

    soup = _parse_with_lxml(html)
    if not soup:
        return None

    dic = {'word': word, 'pronunciation': '', 'paraphrase': [], 'desc': [], 'sentence': []}

    # Pronunciation (Pinyin)
    pinyin = ss(soup, '#phrsListTab .phonetic')
    if pinyin:
        dic['pronunciation'] = pinyin[0].text.strip()

    # Paraphrase (Basic English translation)
    paraphrase_items = ss(soup, '#phrsListTab .trans-container ul li')
    dic['paraphrase'] = [li.text.strip() for li in paraphrase_items]

    # Description (Detailed explanations/definitions in Chinese)
    desc_sections = ss(soup, '#authDictTrans .trans-wrapper')
    for section in desc_sections:
        title_tag = section.find('div', class_='trans-title')
        title = title_tag.text.strip() if title_tag else ''

        examples = []
        example_tags = section.select('.def_row .def_li .def, .def_row .def_li .exp') # Select definition and example lines
        current_def = ''
        for tag in example_tags:
            text = tag.text.strip()
            if 'def' in tag.get('class', []):
                current_def = text
            elif 'exp' in tag.get('class', []) and current_def:
                # Assuming exp follows def, pair them
                examples.append([current_def, text])
                current_def = '' # Reset after pairing
            elif not current_def: # Handle cases where exp might appear first or alone
                 examples.append([text, '']) # Add example without definition pair

        if title or examples:
            dic['desc'].append([title, examples])

    # Sentences (Example sentences)
    sentence_pairs = ss(soup, '#examples .sentence-pair')
    for pair in sentence_pairs[:5]: # Limit to first 5 sentences
        # Structure might differ slightly for Chinese results, adjust selectors if needed
        p_tags = pair.find_all('p', recursive=False)
        if len(p_tags) >= 2:
            zh_s = ''.join(p_tags[0].stripped_strings)
            en_s = ''.join(p_tags[1].stripped_strings)
            dic['sentence'].append([zh_s, en_s])

    # Check if essential info is missing
    if not dic['paraphrase'] and not dic['desc']:
        logging.warning(f"No paraphrase or description found for '{word}' on Youdao.")
        # return None

    return dic
