from akkapros.lib import metrics
import json

text = ("nā~š ḫaṭ~·ṭi ṣīr·ti nā·qid ṣal·mā~t qaq·qa·di rē·ʾû te·nē·šē·ti\n"
        "ī·šum ṭā·bi·ḫu naʾ~·du ša+ana+na·šê kak·kī~·šu ez·zū~·ti qā·tā~·šu as·mā")

wpm = 165
pause_ratio = 30.0

repaired_stats = metrics.analyze_text(text, is_repaired=True)
preprocessed = metrics.preprocess_text(text)
speech = metrics.compute_speech_rate(preprocessed, repaired_stats, wpm, pause_ratio)
pm = metrics.compute_pause_metrics(text, repaired_stats)
pd = metrics.compute_pause_durations(pm, speech, pause_ratio)

print('--- RAW COUNTS ---')
print(json.dumps(pm['raw_counts'], indent=2))
print('\nshort_punctuation_per_syllable =', pm['short_punctuation_per_syllable'])
print('long_punctuation_per_syllable =', pm['long_punctuation_per_syllable'])
print('\n--- SPEECH METRICS ---')
print(json.dumps(speech, indent=2))

# manual steps
sps_speech = speech['sps_speech']
syllable_duration = speech['syllable_duration']
mora_duration = speech['mora_duration']

total_time_per_syllable = 1.0 / sps_speech
pause_time_per_syllable = total_time_per_syllable - syllable_duration

short_per = pm['short_punctuation_per_syllable']
long_per = pm['long_punctuation_per_syllable']
long_w = 2.0

total_pause_units = short_per * 1.0 + long_per * long_w
unit_duration = pause_time_per_syllable / total_pause_units if total_pause_units!=0 else 0
initial_short_duration = unit_duration * 1.0
initial_long_duration = unit_duration * long_w
initial_short_contribution = short_per * initial_short_duration
initial_long_contribution = long_per * initial_long_duration

print('\n--- MANUAL COMPUTATION ---')
print('total_time_per_syllable =', total_time_per_syllable)
print('pause_time_per_syllable =', pause_time_per_syllable)
print('total_pause_units =', total_pause_units)
print('unit_duration =', unit_duration)
print('initial_short_duration =', initial_short_duration)
print('initial_long_duration =', initial_long_duration)
print('initial_short_contribution =', initial_short_contribution)
print('initial_long_contribution =', initial_long_contribution)

short_mora_ratio = initial_short_duration / mora_duration if mora_duration>0 else 0
corrected_short_mora_multiple = int(round(short_mora_ratio / 2.0) * 2)
corrected_short_duration = corrected_short_mora_multiple * mora_duration
initial_total_from_counts = initial_short_duration * pm['raw_counts']['short_punctuation'] + initial_long_duration * pm['raw_counts']['long_punctuation']
if pm['raw_counts']['long_punctuation']>0:
    corrected_long_duration = (initial_total_from_counts - corrected_short_duration * pm['raw_counts']['short_punctuation']) / pm['raw_counts']['long_punctuation']
else:
    corrected_long_duration = initial_long_duration

corrected_short_contribution = short_per * corrected_short_duration
corrected_long_contribution = long_per * corrected_long_duration
corrected_long_weight = corrected_long_duration / corrected_short_duration if corrected_short_duration>0 else 0

print('\nshort_mora_ratio =', short_mora_ratio)
print('corrected_short_mora_multiple =', corrected_short_mora_multiple)
print('corrected_short_duration =', corrected_short_duration)
print('corrected_long_duration =', corrected_long_duration)
print('corrected_short_contribution =', corrected_short_contribution)
print('corrected_long_contribution =', corrected_long_contribution)
print('corrected_long_weight =', corrected_long_weight)

print('\n--- PROGRAM OUTPUT pd ---')
print(json.dumps(pd, indent=2))
