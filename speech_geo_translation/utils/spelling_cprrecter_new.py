import pickle
import fuzzywuzzy
from fuzzywuzzy import process
import itertools
import operator
import copy

WORDS_SET_PKL_PATH = "/home/mohamed/Mohamed/Vodafone_project/projects/app/files/spell_corrector_files/address_wrods_set.pkl"
PROBS_DICTS_PKL_PATH = "/home/mohamed/Mohamed/Vodafone_project/projects/app/files/spell_corrector_files/forward_bacward_probs.pkl"

GOVS_SET = {
    "الجيزه",
    "قنا",
    "القاهرة",
    "اسيوط",
    "الاسكندرية",
    "دمياط",
    "كفر الشيخ",
    "الدقهلية",
    "بورسعيد",
    "الاسماعلية",
    "شمال",
    "سيناء",
    "الوادي",
    "الجديد",
    "الاقصر",
    "الفيوم",
    "سوهاج",
    "البحيرة",
    "جنوب",
    "سيناء",
    "السويس",
    "الشرقية",
    "المنوفية",
    "القليوبية",
    "بنى",
    "سويف",
    "المنيا",
    "اسوان",
    "البحر",
    "الاحمر",
    "الغربية",
    "جيزه",
    "قاهرة",
    "اسكندرية",
    "دمياط",
    "كفر",
    "الشيخ",
    "دقهلية",
    "بورسعيد",
    "اسماعلية",
    "شمال",
    "سيناء",
    "الوادي" "الجديد",
    "اقصر",
    "فيوم",
    "بحيرة",
    "سويس",
    "شرقية",
    "منوفية",
    "قليوبية",
    "بنى سويف",
    "منيا",
    "اسوان",
    "بحر",
    "احمر",
    "مطروح",
    "غربية",
}


class Chunk:
    def __init__(self, words_list, score, words_score, check_size):
        self.chunk_size = len(words_list)
        self.words_list = words_list
        self.score = score
        self.words_score = words_score

        self.last_words_list = words_list[-check_size + 1 :]
        self.first_words_list = words_list[: check_size - 1]
        self.sentence = " ".join(words_list)


class SpellingCorrectorNew:
    """
    Probability based spelling corrector for addressess
    """

    def __init__(
        self,
        words_set_pkl_path=WORDS_SET_PKL_PATH,
        probs_dicts_pkl_path=PROBS_DICTS_PKL_PATH,
    ):

        with open(words_set_pkl_path, "rb") as file:
            self.words_set = pickle.load(file)

        with open(probs_dicts_pkl_path, "rb") as file:
            self.forward_probabilities, self.backward_probabilities = pickle.load(file)

    @staticmethod
    def get_potential_words_prob(sentence: str, words_set: set[str], limit: int = 10):
        def inverse_dist(a, b):
            x = fuzzywuzzy.StringMatcher.distance(a, b, weights=(3, 9, 6))
            if x == 0:
                return 1.0
            return 1 / (x)

        input_words_list = sentence.split(" ")
        best_matchs_list = []
        for word in input_words_list:
            best_match1 = process.extractBests(
                word, words_set, scorer=inverse_dist, limit=limit
            )
            best_match2 = process.extractBests(
                word, GOVS_SET, scorer=inverse_dist, limit=limit // 3
            )
            # print(best_match1+best_match2)
            best_matchs_list.append(best_match1 + best_match2)

        return best_matchs_list

    @staticmethod
    def get_chunk_objs_list(
        chunk,
        forward_probabilities,
        backward_probabilities,
        check_size=None,
        spell_probs_weight=1.0,
    ):

        chunk_size = len(chunk)
        if check_size == None:
            check_size = chunk_size

        posibilities = list(itertools.product(*chunk))
        chunk_objs_list = []

        for _, posibility in enumerate(posibilities):

            occur_probs = [0.0 for _ in range(chunk_size)]
            spell_probs = [spell_probs_weight for _ in range(chunk_size)]

            words = []
            words_score = []

            for j, (word, spell_prob) in enumerate(posibility):

                words.append(word)
                words_score.append(spell_prob)

                spell_probs[j] *= spell_prob

                for k in range(j + 1, len(posibility)):

                    occur_probs[j] += forward_probabilities[(word, posibility[k][0])]
                    occur_probs[k] += backward_probabilities[(posibility[k][0], word)]

            probs = list(map(operator.mul, occur_probs, spell_probs))

            all_probs = 0
            for prob in probs:
                all_probs += prob
            all_probs /= chunk_size

            chunk_obj = Chunk(words, all_probs, words_score, check_size=check_size)

            chunk_objs_list.append(chunk_obj)

        return chunk_objs_list

    def get_sentece_chunks(self, sentence, chunk_size=3):
        potential_words = self.get_potential_words_prob(
            sentence, words_set=self.words_set, limit=8
        )
        list_of_chunk_objs_list = []
        for i in range(len(potential_words) - chunk_size + 1):
            chunk_objs_list = self.get_chunk_objs_list(
                potential_words[i : chunk_size + i],
                self.forward_probabilities,
                self.backward_probabilities,
                spell_probs_weight=1.0,
            )
            list_of_chunk_objs_list.append(chunk_objs_list)
        return list_of_chunk_objs_list

    def merge_chunks_bacward(self, chunk, beam_leafs, check_size):
        tranformed_chunk = []
        curr = []
        for leaf in beam_leafs:
            curr.append((leaf.words_list[0], leaf.words_score[0]))

        tranformed_chunk.append(curr)

        for i in range(0, chunk.chunk_size):
            tranformed_chunk.append([(chunk.words_list[i], chunk.words_score[i])])

        return self.get_chunk_objs_list(
            tranformed_chunk,
            self.forward_probabilities,
            self.backward_probabilities,
            check_size=check_size,
            spell_probs_weight=1.0,
        )

    def merge_chunks_forward(self, chunk, beam_leafs, check_size):
        tranformed_chunk = []

        for i in range(0, chunk.chunk_size):
            tranformed_chunk.append([(chunk.words_list[i], chunk.words_score[i])])

        curr = []
        for leaf in beam_leafs:
            curr.append((leaf.words_list[-1], leaf.words_score[-1]))

        tranformed_chunk.append(curr)

        return self.get_chunk_objs_list(
            tranformed_chunk,
            self.forward_probabilities,
            self.backward_probabilities,
            check_size=check_size,
            spell_probs_weight=1.0,
        )

    def beam_search(self, list_of_chunk_objs_list, top_k=5, chunk_size=3):
        size = len(list_of_chunk_objs_list)
        all_bests = []
        for i in range(size):
            # Get best k
            best_k = sorted(
                list_of_chunk_objs_list[i], key=lambda x: x.score, reverse=True
            )[:top_k]
            curr_best_k = copy.deepcopy(best_k)
            direction = True
            fi = i + 1
            bi = i - 1
            while fi < size and bi >= 0:
                new_best_k = []
                if direction:
                    for j, chunk in enumerate(curr_best_k):
                        # Filter from back
                        beam_leafs = list(
                            filter(
                                lambda x: x.last_words_list == chunk.first_words_list,
                                list_of_chunk_objs_list[bi],
                            )
                        )
                        beam_leafs = sorted(
                            beam_leafs, key=lambda x: x.score, reverse=True
                        )[:top_k]
                        # Merge chunk with beam leafs
                        new_best_k += self.merge_chunks_bacward(
                            chunk, beam_leafs, check_size=chunk_size
                        )

                    bi -= 1

                else:
                    for j, chunk in enumerate(curr_best_k):
                        # Filter from back
                        beam_leafs = list(
                            filter(
                                lambda x: x.first_words_list == chunk.last_words_list,
                                list_of_chunk_objs_list[fi],
                            )
                        )
                        beam_leafs = sorted(
                            beam_leafs, key=lambda x: x.score, reverse=True
                        )[:top_k]
                        # Merge chunk with beam leafs
                        new_best_k += self.merge_chunks_forward(
                            chunk, beam_leafs, check_size=chunk_size
                        )
                    fi += 1

                direction = not direction
                curr_best_k = sorted(new_best_k, key=lambda x: x.score, reverse=True)[
                    :top_k
                ]

            while fi < size:
                new_best_k = []
                for j, chunk in enumerate(curr_best_k):
                    # Filter from back
                    beam_leafs = list(
                        filter(
                            lambda x: x.first_words_list == chunk.last_words_list,
                            list_of_chunk_objs_list[fi],
                        )
                    )
                    beam_leafs = sorted(
                        beam_leafs, key=lambda x: x.score, reverse=True
                    )[:top_k]
                    # Merge chunk with beam leafs
                    new_best_k += self.merge_chunks_forward(
                        chunk, beam_leafs, check_size=chunk_size
                    )
                fi += 1

                curr_best_k = sorted(new_best_k, key=lambda x: x.score, reverse=True)[
                    :top_k
                ]

            while bi >= 0:
                new_best_k = []
                for j, chunk in enumerate(curr_best_k):
                    # Filter from back
                    beam_leafs = list(
                        filter(
                            lambda x: x.last_words_list == chunk.first_words_list,
                            list_of_chunk_objs_list[bi],
                        )
                    )
                    beam_leafs = sorted(
                        beam_leafs, key=lambda x: x.score, reverse=True
                    )[:top_k]
                    # Merge chunk with beam leafs
                    new_best_k += self.merge_chunks_bacward(
                        chunk, beam_leafs, check_size=chunk_size
                    )
                bi -= 1

                curr_best_k = sorted(new_best_k, key=lambda x: x.score, reverse=True)[
                    :top_k
                ]

            all_bests += curr_best_k

        return sorted(all_bests, key=lambda x: x.score, reverse=True)[:top_k]

    def __call__(self, sentence: str):
        chunks = self.get_sentece_chunks(sentence, chunk_size=3)
        result = self.beam_search(chunks, top_k=3, chunk_size=3)

        return result[0].sentence
