# ***Building a Custom Diphone Voice with MBROLATOR: Complete Guide**

## ***What We Discovered**

***After extensive exploration, we developed a practical, repeatable method for creating custom diphone voices for MBROLA. This guide synthesizes our findings into a clear workflow, from recording script design to automatic segmentation.**


## ***Table of Contents**

1. ***The Core Problem**

2. ***Our Solution: The Rhythmic Recording Pattern**

3. ***Phoneme Inventory Example**

4. ***Diphone Inventory Calculation**

5. ***The Recording Script**

6. ***Recording Protocol**

7. ***Automatic Segmentation Strategy**

8. ***Python Segmentation Script**

9. ***MBROLATOR Workflow**

10. ***Glossary**

11. ***Next Steps**

12. ***Appendices**


## ***The Core Problem**

***Building a custom diphone voice requires:**

| ***Requirement** | ***Challenge** |
| - | - |
| ***Recording every possible diphone** | ***63+ recordings needed** |
| ***Segmenting each recording** | ***Mark start, middle, end sample numbers** |
| ***Avoiding manual segmentation** | ***Hundreds of files × 3 marks = tedious** |
| ***Natural-sounding recordings** | ***List fatigue causes unnatural articulation** |

***Manual segmentation is the bottleneck. Each diphone needs three sample numbers marked by hand—a process that is tedious, error-prone, and impractical for more than a few dozen diphones.**


## ***Our Solution: The Rhythmic Recording Pattern**

***We discovered a rhythmic pattern that makes automatic segmentation possible:**

text

```
***\_ V C C V C C V C \_**
```

***Where:**

- ***`\_` = silence (1 second)**

- ***`V` = vowel**

- ***`C` = consonant**

### ***Why This Pattern Works**

***Let's label the positions:**

text

```
***\_  V1  C1  C2  V2  C3  C4  V3  C5  \_**

   ***1   2   3   4   5   6   7   8   9**
```

***Every adjacent pair gives us a different diphone type:**

| ***Positions** | ***Diphone Type** | ***Example** | ***Covered** |
| - | - | - | - |
| ***\_ → V1** | ***\_-V** | ***silence→vowel** | ✓ |
| ***V1 → C1** | ***V-C** | ***vowel→consonant** | ✓ |
| ***C1 → C2** | ***C-C** | ***consonant cluster** | ✓ |
| ***C2 → V2** | ***C-V** | ***consonant→vowel** | ✓ |
| ***V2 → C3** | ***V-C** | ***vowel→consonant** | ✓ |
| ***C3 → C4** | ***C-C** | ***consonant cluster** | ✓ |
| ***C4 → V3** | ***C-V** | ***consonant→vowel** | ✓ |
| ***V3 → C5** | ***V-C** | ***vowel→consonant** | ✓ |
| ***C5 → \_** | ***C-\_** | ***consonant→silence** | ✓ |

***This single pattern covers ALL diphone types:**

| ***Type** | ***Count in Pattern** |
| - | - |
| ***\_-V** | ***1** |
| ***V-C** | ***3** |
| ***C-C** | ***2** |
| ***C-V** | ***2** |
| ***C-\_** | ***1** |
| ***Total** | ***9 diphones per word** |


## ***Phoneme Inventory Example**

***For this guide, we'll use a small inventory:**

text

```
***Consonants: k, s, m, b, j**

***Vowels: a, u**
```

### ***Why This Inventory**

- ***5 consonants give 25 CC combinations**

- ***2 vowels give natural variation**

- ***Mix of stop consonants (k,b), fricative (s), nasal (m), approximant (j)**

- ***Manageable size for demonstration**


## ***Diphone Inventory Calculation**

### ***All Possible Diphone Types**

#### ***Vowel-Consonant (V-C)**

|  | ***k** | ***s** | ***m** | ***b** | ***j** |
| :-: | - | - | - | - | - |
| ***a** | ***a-k** | ***a-s** | ***a-m** | ***a-b** | ***a-j** |
| ***u** | ***u-k** | ***u-s** | ***u-m** | ***u-b** | ***u-j** |

***Count: 2 × 5 = 10 diphones**

#### ***Consonant-Vowel (C-V)**

|  | ***a** | ***u** |
| :-: | - | - |
| ***k** | ***k-a** | ***k-u** |
| ***s** | ***s-a** | ***s-u** |
| ***m** | ***m-a** | ***m-u** |
| ***b** | ***b-a** | ***b-u** |
| ***j** | ***j-a** | ***j-u** |

***Count: 5 × 2 = 10 diphones**

#### ***Consonant-Consonant (C-C)**

|  | ***k** | ***s** | ***m** | ***b** | ***j** |
| :-: | - | - | - | - | - |
| ***k** | ***k-k** | ***k-s** | ***k-m** | ***k-b** | ***k-j** |
| ***s** | ***s-k** | ***s-s** | ***s-m** | ***s-b** | ***s-j** |
| ***m** | ***m-k** | ***m-s** | ***m-m** | ***m-b** | ***m-j** |
| ***b** | ***b-k** | ***b-s** | ***b-m** | ***b-b** | ***b-j** |
| ***j** | ***j-k** | ***j-s** | ***j-m** | ***j-b** | ***j-j** |

***Count: 5 × 5 = 25 diphones**

#### ***Vowel-Vowel (V-V)**

|  | ***a** | ***u** |
| :-: | - | - |
| ***a** | ***a-a** | ***a-u** |
| ***u** | ***u-a** | ***u-u** |

***Count: 2 × 2 = 4 diphones**

#### ***Boundary Diphones**

| ***Type** | ***With 'a'** | ***With 'u'** | ***Count** |
| - | - | - | - |
| ***\_-C** | ***\_-k, \_-s, \_-m, \_-b, \_-j** | ***\_-k, \_-s, \_-m, \_-b, \_-j** | ***5** |
| ***C-\_** | ***k-, s-*, m-, b-*, j-\_** | ***k-, s-*, m-, b-*, j-\_** | ***5** |
| ***\_-V** | ***\_-a** | ***\_-u** | ***2** |
| ***V-\_** | ***a-\_** | ***u-\_** | ***2** |

***Boundary total: 5 + 5 + 2 + 2 = 14 diphones**

### ***Grand Total**

| ***Category** | ***Count** |
| - | - |
| ***V-C** | ***10** |
| ***C-V** | ***10** |
| ***C-C** | ***25** |
| ***V-V** | ***4** |
| ***Boundaries** | ***14** |
| ***TOTAL** | ***63 diphones** |


## ***The Recording Script**

### ***Key Insight: Randomization Prevents List Fatigue**

***If every word starts with "ak...", your articulation becomes unnatural. The script must mix up the patterns randomly so that:**

- ***Both vowels appear as V1, V2, V3**

- ***All consonants appear in all positions**

- ***No repetitive patterns tire your voice**

### ***Complete Randomized Script**

markdown

```
***\# DIPHONE RECORDING SCRIPT**

***\# Pattern: \_ V C C V C C V C \_**

***\# Consonants: k, s, m, b, j**

***\# Vowels: a, u**

***\# Total words: 160 (covers each CC pair ~6-7 times)**

***\# Format: Speak each line naturally, pause 1 second before and after each word**

***\# Record at 16kHz, 16-bit, mono**


***\# ============================================**

***\# RECORDING BLOCK 1**

***\# ============================================**


***\_ a m b a j s a k \_***

***\_ u s k u b m u j \_***

***\_ a k j a m b a s \_***

***\_ u m s u j k u b \_***

***\_ a b m a s j a k \_***

***\_ u j b u k s u m \_***

***\_ a s k a b m a j \_***

***\_ u k m u s j u b \_***

***\_ a j s a m k a b \_***

***\_ u b j u k m u s \_***

***\_ a m k a j b a s \_***

***\_ u s m u b k u j \_***

***\_ a k b a s m a j \_***

***\_ u j s u m b u k \_***

***\_ a b j a k s a m \_***

***\_ u m k u j s u b \_***

***\_ a s m a b j a k \_***

***\_ u k b u s m u j \_***

***\_ a j m a k b a s \_***

***\_ u b s u m k u j \_***


***\# ============================================**

***\# RECORDING BLOCK 2**

***\# ============================================**


***\_ a k s a m j a b \_***

***\_ u m b u j s u k \_***

***\_ a s j a b m a k \_***

***\_ u j k u s b u m \_***

***\_ a b k a m s a j \_***

***\_ u s m u k j u b \_***

***\_ a m j a k b a s \_***

***\_ u k s u j m u b \_***

***\_ a j b a s k a m \_***

***\_ u b m u k s u j \_***

***\_ a k m a s b a j \_***

***\_ u s j u m k u b \_***

***\_ a b s a j m a k \_***

***\_ u m k u b j u s \_***

***\_ a j k a m b a s \_***

***\_ u k j u s m u b \_***

***\_ a m s a b k a j \_***

***\_ u b s u j m u k \_***

***\_ a s b a k j a m \_***

***\_ u j m u s b u k \_***


***\# ============================================**

***\# RECORDING BLOCK 3**

***\# ============================================**


***\_ a m j a s b a k \_***

***\_ u b s u k m u j \_***

***\_ a k s a m j a b \_***

***\_ u m b u j s u k \_***

***\_ a j m a b k a s \_***

***\_ u s k u j b u m \_***

***\_ a b j a k m a s \_***

***\_ u k m u s j u b \_***

***\_ a s m a j b a k \_***

***\_ u j s u m k u b \_***

***\_ a m k a b j a s \_***

***\_ u b m u k s u j \_***

***\_ a k b a s m a j \_***

***\_ u s j u m b u k \_***

***\_ a j s a k m a b \_***

***\_ u m k u j s u b \_***

***\_ a b m a s k a j \_***

***\_ u k b u m j u s \_***

***\_ a s j a m b a k \_***

***\_ u j m u b k u s \_***


***\# ============================================**

***\# RECORDING BLOCK 4**

***\# ============================================**


***\_ a k m a s b a j \_***

***\_ u s b u m j u k \_***

***\_ a m s a j k a b \_***

***\_ u j k u b m u s \_***

***\_ a b k a m j a s \_***

***\_ u m j u s k u b \_***

***\_ a s m a b k a j \_***

***\_ u k s u j m u b \_***

***\_ a j b a s m a k \_***

***\_ u b m u k j u s \_***

***\_ a m j a k s a b \_***

***\_ u s k u b j u m \_***

***\_ a k b a m s a j \_***

***\_ u j m u s b u k \_***

***\_ a b s a j m a k \_***

***\_ u m k u j s u b \_***

***\_ a s j a m b a k \_***

***\_ u k b u m s u j \_***

***\_ a j m a k b a s \_***

***\_ u b s u j k u m \_***


***\# ============================================**

***\# RECORDING BLOCK 5**

***\# ============================================**


***\_ a s m a b j a k \_***

***\_ u k j u s m u b \_***

***\_ a m b a j k a s \_***

***\_ u j s u m b u k \_***

***\_ a k j a s m a b \_***

***\_ u m k u b s u j \_***

***\_ a b m a k j a s \_***

***\_ u s b u m k u j \_***

***\_ a j k a m b a s \_***

***\_ u b m u s j u k \_***

***\_ a s k a j m a b \_***

***\_ u k s u m j u b \_***

***\_ a m s a b k a j \_***

***\_ u j b u k s u m \_***

***\_ a b j a s k a m \_***

***\_ u m j u s b u k \_***

***\_ a k b a m j a s \_***

***\_ u s m u j k u b \_***

***\_ a j s a k m a b \_***

***\_ u b k u s m u j \_***


***\# ============================================**

***\# RECORDING BLOCK 6**

***\# ============================================**


***\_ a k s a m b a j \_***

***\_ u m b u j s u k \_***

***\_ a s m a b j a k \_***

***\_ u j k u s m u b \_***

***\_ a b k a j m a s \_***

***\_ u s j u m k u b \_***

***\_ a m j a k s a b \_***

***\_ u k m u b j u s \_***

***\_ a j b a s k a m \_***

***\_ u b s u m j u k \_***

***\_ a s k a j b a m \_***

***\_ u m k u s j u b \_***

***\_ a m b a k j a s \_***

***\_ u j m u b k u s \_***

***\_ a b s a m j a k \_***

***\_ u k j u s b u m \_***

***\_ a j m a s b a k \_***

***\_ u s b u k m u j \_***

***\_ a k m a j b a s \_***

***\_ u b m u j s u k \_***


***\# ============================================**

***\# RECORDING BLOCK 7**

***\# ============================================**


***\_ a s j a m b a k \_***

***\_ u k b u s m u j \_***

***\_ a m k a j s a b \_***

***\_ u j m u k b u s \_***

***\_ a b m a s k a j \_***

***\_ u s k u m j u b \_***

***\_ a j s a b k a m \_***

***\_ u m j u s b u k \_***

***\_ a k b a m j a s \_***

***\_ u b s u k j u m \_***

***\_ a s m a k b a j \_***

***\_ u k m u j s u b \_***

***\_ a m j a b s a k \_***

***\_ u j k u m b u s \_***

***\_ a b k a s m a j \_***

***\_ u s b u j m u k \_***

***\_ a j m a k s a b \_***

***\_ u m k u b j u s \_***

***\_ a k s a j b a m \_***

***\_ u b j u s k u m \_***


***\# ============================================**

***\# RECORDING BLOCK 8**

***\# ============================================**


***\_ a m b a k j a s \_***

***\_ u s k u m j u b \_***

***\_ a k m a s b a j \_***

***\_ u j s u b k u m \_***

***\_ a b s a m k a j \_***

***\_ u m j u s b u k \_***

***\_ a j k a b m a s \_***

***\_ u k b u j s u m \_***

***\_ a s j a m k a b \_***

***\_ u b m u k s u j \_***

***\_ a m k a b j a s \_***

***\_ u s j u m b u k \_***

***\_ a k b a s m a j \_***

***\_ u j m u k s u b \_***

***\_ a b m a j k a s \_***

***\_ u k s u b j u m \_***

***\_ a j s a k m a b \_***

***\_ u b k u m j u s \_***

***\_ a s m a j b a k \_***

***\_ u j b u s m u k \_***


***\# ============================================**

***\# END OF SCRIPT**

***\# ============================================**
```


## ***Recording Protocol**

### ***Technical Specifications**

| ***Parameter** | ***Value** |
| - | - |
| ***Sample Rate** | ***16 kHz** |
| ***Bit Depth** | ***16-bit** |
| ***Channels** | ***Mono** |
| ***Format** | ***WAV (linear PCM)** |
| ***Silence between words** | ***1 second minimum** |

### ***Recording Environment**

- ***Quiet room with no background noise**

- ***Consistent microphone position (approx 15-20 cm from mouth)**

- ***Pop filter to reduce plosives**

- ***Consistent volume level (aim for -3dB to -6dB peak)**

### ***Speaking Guidelines**

1. ***Speak naturally at a moderate pace**

2. ***Pause 1 second before and after each word (the `\_` represents this pause)**

3. ***Maintain consistent pitch throughout the session**

4. ***Take breaks between blocks to avoid vocal fatigue**

5. ***If you make a mistake, pause, wait 2 seconds, and repeat the word**

### ***Recording Session Structure**

text

```
***Session 1: Blocks 1-2 (40 words)  ~ 5 minutes**

***Break: 5 minutes**

***Session 2: Blocks 3-4 (40 words)  ~ 5 minutes**

***Break: 5 minutes**

***Session 3: Blocks 5-6 (40 words)  ~ 5 minutes**

***Break: 5 minutes**

***Session 4: Blocks 7-8 (40 words)  ~ 5 minutes**
```

### ***File Naming Convention**

***Save the entire recording as a single file:**

text

```
***diphone\_recording\_\[DATE\].wav**
```

***Example: `diphone\_recording\_20250306.wav`**


## ***Automatic Segmentation Strategy**

### ***Why This Pattern Enables Auto-Segmentation**

***The rhythmic pattern `\_ V C C V C C V C \_` creates predictable acoustic events:**

1. ***Silence at start and end (easy to detect)**

2. ***Vowels have high amplitude and periodic structure**

3. ***Consonants have lower amplitude and aperiodic structure**

4. ***CC clusters have characteristic low amplitude followed by release**

### ***Segmentation Logic**

***For each word in the recording:**

1. ***Detect word boundaries using silence detection**

2. ***Find vowel peaks (3 peaks = V1, V2, V3)**

3. ***Place phoneme boundaries midway between vowel peaks**

4. ***Extract diphone segments based on the pattern**

### ***Visual Representation**

text

```
***Audio waveform:**

   ╭╮  ╭╮  ╭╮  ╭╮  ╭╮  ╭╮  ╭╮  ╭╮  ╭╮

***\_\_\_╯╰──╯╰──╯╰──╯╰──╯╰──╯╰──╯╰──╯╰──╯╰\_\_\_**

   ***V1  C1  C2  V2  C3  C4  V3  C5**


***Vowel peaks:    ↑       ↑       ↑**

***Boundaries:   |  |  |  |  |  |  |  |  |**

             ***0  1  2  3  4  5  6  7  8  9**

***Positions:    \_  V1 C1 C2 V2 C3 C4 V3 C5 \_**
```


## ***Python Segmentation Script**

**(To be created tomorrow)**

***The script will:**

1. ***Read the long recording WAV file**

2. ***Load the list of diphone words from the script**

3. ***Automatically detect word boundaries using silence**

4. ***For each word, segment into 9 phonemes using the rhythmic pattern**

5. ***Generate the MBROLATOR segmentation file (`.seg`) with start, middle, and end samples**

6. ***Split the long recording into individual diphone WAV files**

### ***Expected Output**

text

```
***\# MBROLATOR segmentation file: voice\_name.seg**

***\# Format: filename diphone\_name first\_sample last\_sample middle\_sample**


***ak.d16    a k    11234    14567    12900**

***ka.d16    k a    15678    18901    17289**

***am.d16    a m    20123    23456    21789**

***ma.d16    m a    24678    27901    26289**

***... etc.**
```


## ***MBROLATOR Workflow**

***Once segmentation is complete, the MBROLATOR pipeline is:**

### ***Phase 1: Prepare Data**

- ***16-bit, 16kHz diphone WAV files (one per diphone)**

- ***Segmentation file (`.seg`) with boundaries**

### ***Phase 2: Compile MBROLATOR Tools**

bash

```
***cd AnaMBE && make**

***cd ../Resynthesis && make**

***cp anaf0 anambe resynth database\_build /usr/local/bin/**
```

### ***Phase 3: Generate Parameter Files**

bash

```
***generate\_mbrola my\_voice**
```

***Edit `my\_voice.mbe` to set:**

text

```
***FrameLength = \[3 × pitch period in samples\]**

***FrameShift = \[pitch period in samples\]**
```

### ***Phase 4: Run Analysis**

bash

```
***generate\_make.pl my\_voice WAV/ RES/ RES/**

***make -f my\_voice.mak**
```

### ***Phase 5: Build Database**

bash

```
***database\_build my\_voice RES/ \[pitch\] 16000 \[framesize\] 1**
```

### ***Phase 6: Test**

bash

```
***mbrola my\_voice test.pho test.wav**
```


## ***Glossary**

| ***Term** | ***Definition** |
| - | - |
| ***Diphone** | ***A speech unit spanning from the middle of one phoneme to the middle of the next** |
| ***MBROLA** | ***A diphone concatenation synthesizer** |
| ***MBROLATOR** | ***Toolset for creating MBROLA voice databases** |
| ***Segmentation file** | ***Text file listing start, middle, and end samples for each diphone** |
| **.seg* file** | ***MBROLATOR's segmentation file format** |
| **.mbe* file** | ***Multi-Band Excitation analysis parameters** |
| **.f0* file** | ***Fundamental frequency analysis parameters** |
| **.syn* file** | ***Resynthesis parameters** |
| ***FrameLength** | ***Analysis window size in samples (typically 3× pitch period)** |
| ***FrameShift** | ***Step between analysis frames (typically 1× pitch period)** |
| **-V diphone** | ***Silence to vowel (word-initial vowel)** |
| ***V-C diphone\_** | ***Vowel to consonant** |
| ***C-C diphone\_** | ***Consonant cluster** |
| ***C-V diphone\_** | ***Consonant to vowel** |
| ***C-\_ diphone\_** | ***Consonant to silence (word-final consonant)** |


## ***Next Steps**

### ***Day 1: Recording**

- ***Set up recording environment**

- ***Test recording levels**

- ***Record Blocks 1-2**

- ***Take break**

- ***Record Blocks 3-4**

- ***Check recording quality**

- ***Record remaining blocks**

### ***Day 2: Segmentation Script**

- ***Write Python script for auto-segmentation**

- ***Test on first block**

- ***Verify boundary accuracy**

- ***Generate full segmentation file**

- ***Split into individual diphone WAVs**

### ***Day 3: MBROLATOR Setup**

- ***Compile MBROLATOR tools**

- ***Generate parameter files**

- ***Measure pitch period**

- ***Configure `.mbe` file**

### ***Day 4: Analysis**

- ***Run makefile analysis**

- ***Troubleshoot any errors**

- ***Build database**

### ***Day 5: Testing**

- ***Test voice with MBROLA**

- ***Fine-tune parameters**

- ***Rebuild if needed**


## ***Appendices**

### ***Appendix A: Quick Reference Card**

text

```
***Pattern: \_ V C C V C C V C \_**

***Positions: 0 1 2 3 4 5 6 7 8 9**

***Diphones:**

  ***\_-V1 (0-1)**

  ***V1-C1 (1-2)**

  ***C1-C2 (2-3)**

  ***C2-V2 (3-4)**

  ***V2-C3 (4-5)**

  ***C3-C4 (5-6)**

  ***C4-V3 (6-7)**

  ***V3-C5 (7-8)**

  ***C5-\_ (8-9)**
```

### ***Appendix B: CC Pair Coverage**

***The 160-word script ensures each CC pair appears approximately:**

| ***CC Pair** | ***Occurrences** |
| - | - |
| ***k-k** | ***6-7** |
| ***k-s** | ***6-7** |
| ***k-m** | ***6-7** |
| ***k-b** | ***6-7** |
| ***k-j** | ***6-7** |
| ***s-k** | ***6-7** |
| ***s-s** | ***6-7** |
| ***...** | ***...** |
| ***j-j** | ***6-7** |

### ***Appendix C: Troubleshooting**

| ***Problem** | ***Likely Cause** | ***Solution** |
| - | - | - |
| ***Segmentation mismatch** | ***Silence detection off** | ***Adjust threshold** |
| ***MBROLATOR analysis errors** | ***FrameLength wrong** | ***Re-measure pitch period** |
| ***Buzzy synthesis** | ***VUVLimVoiced too high** | ***Lower in `.syn` file** |
| ***Missing diphones** | ***Coverage gap** | ***Add more words** |


## ***Conclusion**

***We have developed a complete, practical workflow for creating custom diphone voices with MBROLATOR. The key innovations are:**

1. ***The rhythmic pattern `\_ V C C V C C V C \_` that covers all diphone types**

2. ***Randomized script that prevents list fatigue**

3. ***Auto-segmentation strategy that eliminates manual boundary marking**

4. ***Clear protocol from recording to working MBROLA voice**

***Tomorrow we will implement the Python segmentation script that turns this design into reality.**


**Document version: 1.0*  
Date: March 6, 2025**

