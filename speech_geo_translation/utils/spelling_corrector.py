import pickle
import fuzzywuzzy
from fuzzywuzzy import process
import itertools
import operator

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
    def __init__(self, chunk_size, words_list, score, words_score):
        self.chunk_size = chunk_size
        self.words_list = words_list
        self.score = score
        self.words_score = words_score

        self.last_words_list = words_list[-chunk_size + 1 :]
        self.first_words_list = words_list[: chunk_size - 1]
        self.sentence = " ".join(words_list)


class SpellingCorrector:
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
            x = fuzzywuzzy.StringMatcher.distance(a, b, weights=(1, 6, 3))
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
            best_matchs_list.append(best_match1 + best_match2)

        return best_matchs_list

    @staticmethod
    def get_potential_sentences_probabilities(
        potential_words_list,
        forward_probabilities,
        backward_probabilities,
        chunk_size=3,
        beam_size=5,
    ):
        def get_chunk_probability(
            chunk,
            forward_probabilities,
            backward_probabilities,
            top_k=5,
            spell_probs_weight=5.0,
        ):

            chunk_size = len(chunk)

            posibilities = list(itertools.product(*chunk))
            posibilities_with_probs = []

            for _, posibility in enumerate(posibilities):

                occur_probs = [0.0 for _ in range(chunk_size)]
                spell_probs = [spell_probs_weight for _ in range(chunk_size)]

                words = []

                for j, (word, spell_prob) in enumerate(posibility):

                    words.append(word)

                    spell_probs[j] *= spell_prob

                    for k in range(j + 1, len(posibility)):

                        occur_probs[j] += forward_probabilities[
                            (word, posibility[k][0])
                        ]
                        occur_probs[k] += backward_probabilities[
                            (posibility[k][0], word)
                        ]

                probs = list(map(operator.mul, occur_probs, spell_probs))

                all_probs = 0
                for prob in probs:
                    all_probs += prob
                all_probs /= chunk_size

                posibilities_with_probs.append((" ".join(words), all_probs))

            return sorted(posibilities_with_probs, key=lambda x: x[1], reverse=True)[
                :top_k
            ]

        words_len = len(potential_words_list)
        curr_sequnces = get_chunk_probability(
            potential_words_list[: min(words_len, chunk_size)],
            forward_probabilities,
            backward_probabilities,
            top_k=beam_size,
        )
        if words_len <= chunk_size:
            return curr_sequnces

        for i in range(chunk_size - 1, words_len, chunk_size - 1):
            curr_last_words = set()
            for seq, prob in curr_sequnces:
                curr_last_words.add(seq.split(" ")[-1])

            filtered_grams = list(
                filter(lambda x: x[0] in curr_last_words, potential_words_list[i])
            )
            curr_chunk = [filtered_grams] + potential_words_list[i + 1 : i + chunk_size]

            new_sequnces = get_chunk_probability(
                curr_chunk,
                forward_probabilities,
                backward_probabilities,
                top_k=beam_size,
            )

            cross_sequnces = []

            for sequnce_new, prob_new in new_sequnces:
                for sequnce_curr, prob_curr in curr_sequnces:
                    if sequnce_curr.split(" ")[-1] == sequnce_new.split(" ")[0]:
                        prob = prob_new * prob_curr
                        sequnce = " ".join(
                            sequnce_curr.split(" ") + sequnce_new.split(" ")[1:]
                        )
                        cross_sequnces.append((sequnce, prob))

            curr_sequnces = sorted(cross_sequnces, key=lambda x: x[1], reverse=True)[
                :beam_size
            ]

        return curr_sequnces

    def __call__(
        self, sentence: str, potential_words_limit=10, chunk_size=3, beam_size=6
    ):
        potential_words = self.get_potential_words_prob(
            sentence, self.words_set, limit=potential_words_limit
        )
        # print(potential_words[-1])
        potential_sentences = self.get_potential_sentences_probabilities(
            potential_words,
            self.forward_probabilities,
            self.backward_probabilities,
            chunk_size=chunk_size,
            beam_size=beam_size,
        )
        ref_words = (
            sentence.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").split(" ")
        )
        potential_sentence = potential_sentences[0]
        sen = (
            potential_sentence[0].replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
        )
        print("here", sen)
        substitutions = sum(
            1 for ref, hyp in zip(ref_words, sen.split(" ")) if ref != hyp
        )
        if substitutions == 0:
            return potential_sentence[0]
        elif substitutions <= 2:
            if potential_sentence[1] > 1.0:
                return potential_sentence[0]
        else:
            return None

        return None
