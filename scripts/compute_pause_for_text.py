from akkapros.lib import metrics
import json
text = "nāš ḫaṭ·ṭi ṣīr·ti nā·qid ṣal·māt qaq·qa·di rē·ʾû te·nē·šē·ti\nī·šum ṭā·bi·ḫu naʾ·du ša+ana+na·šê kak·kī·šu ez·zū·ti qā·tā~·šu as·mā"
res = metrics.process_filetext(text, wpm=165, pause_ratio=30)
pd = res['repaired']['pause_durations']
pm = res['repaired']['pause_metrics']
keys = ['initial_long_punctuation_duration','initial_short_punctuation_contribution','initial_long_punctuation_contribution','initial_short_punctuation_percent','initial_long_punctuation_percent','short_punct_weight','initial_long_punct_weight','short_mora_ratio_initial','corrected_short_mora_multiple','corrected_short_punctuation_duration','corrected_long_punctuation_duration','corrected_short_punctuation_contribution','corrected_long_punctuation_contribution','corrected_short_punctuation_percent','corrected_long_punctuation_percent','corrected_long_punct_weight','total_pause_time','pause_time_per_syllable','short_event_count','long_event_count','short_punctuation_duration','long_punctuation_duration','short_punctuation_percent','long_punctuation_percent']
out = {k: pd.get(k) for k in keys}
print(json.dumps(out, indent=2, ensure_ascii=False))
print('raw_counts:', json.dumps(pm['raw_counts'], indent=2, ensure_ascii=False))
