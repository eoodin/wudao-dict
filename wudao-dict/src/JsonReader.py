# -*- coding: utf-8 -*-
import json
import zlib
from collections import defaultdict
from difflib import SequenceMatcher


class JsonReader:
    def __init__(self):
        self.__main_dict = {}
        self.FILE_NAME = './dict/en.z'
        self.INDEX_FILE_NAME = './dict/en.ind'
        self.ZH_FILE_NAME = './dict/zh.z'
        self.ZH_INDEX_FILE_NAME = './dict/zh.ind'
        self.__index_dict = {}
        self.__zh_index_dict = {}
        self._en_buckets = defaultdict(list)
        with open(self.INDEX_FILE_NAME, 'r') as f:
            lines = f.readlines()
            prev_word, prev_no = lines[0].split('|')
            for v in lines[1:]:
                word, no = v.split('|')
                self.__index_dict[prev_word] = (int(prev_no), int(no) - int(prev_no))
                prev_word, prev_no = word, no
            self.__index_dict[word] = (int(no), f.tell() - int(no))
        for w in self.__index_dict:
            if w:
                self._en_buckets[(len(w), w[0])].append(w)
        with open(self.ZH_INDEX_FILE_NAME, 'r') as f:
            lines = f.readlines()
            prev_word, prev_no = lines[0].split('|')
            for v in lines[1:]:
                word, no = v.split('|')
                self.__zh_index_dict[prev_word] = (int(prev_no), int(no) - int(prev_no))
                prev_word, prev_no = word, no
            self.__zh_index_dict[word] = (int(no), f.tell() - int(no))

    def _en_fuzzy_suggestions(self, query, limit=10):
        """Up to ``limit`` English headwords similar to ``query`` (typos / spelling)."""
        query = (query or '').strip().lower()
        if len(query) < 3:
            return []
        L = len(query)
        fc = query[0]
        cands = []
        for delta in (-2, -1, 0, 1, 2):
            ln = L + delta
            if ln < 1:
                continue
            cands.extend(self._en_buckets.get((ln, fc), []))
        min_best_ratio = 0.65 if L <= 7 else 0.58
        ratio_floor = 0.52
        max_pool = 4500
        if len(cands) < 45:
            seen = set(cands)
            for delta in (-2, -1, 0, 1, 2):
                ln = L + delta
                if ln < 1:
                    continue
                for c in 'abcdefghijklmnopqrstuvwxyz':
                    for w in self._en_buckets.get((ln, c), []):
                        if w not in seen:
                            seen.add(w)
                            cands.append(w)
                            if len(cands) >= max_pool:
                                break
                    if len(cands) >= max_pool:
                        break
                if len(cands) >= max_pool:
                    break
        scored = []
        for w in cands:
            r = SequenceMatcher(None, query, w).ratio()
            if r >= ratio_floor:
                scored.append((r, w))
        qset = set(query)
        scored.sort(key=lambda x: (
            -x[0],
            len(set(x[1]) - qset),
            abs(len(x[1]) - L),
            x[1],
        ))
        top = scored[:limit]
        if not top or top[0][0] < min_best_ratio:
            return []
        return [{'word': w, 'score': round(r, 2)} for r, w in top]

    # return strings of word info
    def get_word_info(self, query_word):
        with open(self.FILE_NAME, 'rb') as f:
            if query_word in self.__index_dict:
                word_offset = self.__index_dict[query_word]
                f.seek(word_offset[0])
                bytes_obj = f.read(word_offset[1])
                str_obj = zlib.decompress(bytes_obj).decode('utf8')
                list_obj = str_obj.split('|')
                word = {}
                word['word'] = list_obj[0]
                word['id'] = list_obj[1]
                word['pronunciation'] = {}
                if list_obj[2]:
                    word['pronunciation']['美'] = list_obj[2]
                if list_obj[3]:
                    word['pronunciation']['英'] = list_obj[3]
                if list_obj[4]:
                    word['pronunciation'][''] = list_obj[4]
                word['paraphrase'] = json.loads(list_obj[5])
                word['rank'] = list_obj[6]
                word['pattern'] = list_obj[7]
                word['sentence'] = json.loads(list_obj[8])
                return json.dumps(word)
            else:
                fuzzy = self._en_fuzzy_suggestions(query_word)
                if fuzzy:
                    return json.dumps({
                        'fuzzy': True,
                        'query': query_word,
                        'suggestions': fuzzy,
                    })
                return None

    def get_zh_word_info(self, query_word):
        with open(self.ZH_FILE_NAME, 'rb') as f:
            if query_word in self.__zh_index_dict:
                word_offset = self.__zh_index_dict[query_word]
                f.seek(word_offset[0])
                bytes_obj = f.read(word_offset[1])
                str_obj = zlib.decompress(bytes_obj).decode('utf8')
                list_obj = str_obj.split('|')
                word = {}
                word['word'] = list_obj[0]
                word['id'] = list_obj[1]
                word['pronunciation'] = ''
                if list_obj[2]:
                    word['pronunciation'] = list_obj[2]
                word['paraphrase'] = json.loads(list_obj[3])
                word['desc'] = []
                if list_obj[4]:
                    word['desc'] = json.loads(list_obj[4])
                word['sentence'] = []
                if list_obj[5]:
                    word['sentence'] = json.loads(list_obj[5])
                return json.dumps(word)
            else:
                return None

