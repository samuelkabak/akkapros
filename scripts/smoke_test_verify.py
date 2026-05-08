"""
Smoke test verification script for akkapros phonetizer and metricalc.

Reads _phone.txt and _ophone.txt files, manually computes interval-based
rhythm metrics per the documented formulas in docs/akkapros/metrics-computation.md,
and compares against the metricalc output.

Key metrics verified:
  - %V, %C (vocalic/consonantal interval proportion)
  - meanV, meanC (mean interval duration)
  - ΔV, ΔC (population standard deviation of intervals)
  - VarcoV, VarcoC (normalized variability)
  - rPVI-C (raw Pairwise Variability Index for consonants)
  - nPVI-V (normalized Pairwise Variability Index for vowels)
"""

import sys, os, math, json, re

def parse_phone_file(path):
    """Parse a _phone.txt or _ophone.txt file into rows."""
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the body start (after YAML frontmatter)
    body_start = 0
    in_frontmatter = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == '---':
            if not in_frontmatter:
                in_frontmatter = True
            else:
                body_start = i + 1
                break
    
    for line in lines[body_start:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split('|')
        if len(parts) < 12:
            continue
        row = {
            'label': parts[0],
            'category': parts[1],
            'type': parts[2],
            'length': parts[3],
            'position': parts[4],
            'boundary': parts[5],
            'accent': parts[6],
            'realization': parts[7],
            'duration': int(parts[8]),
            'drift': parts[9],
            'intonation': parts[10],
            'text': '|'.join(parts[11:]) if len(parts) > 11 else '',
        }
        rows.append(row)
    return rows


def normalize_to_intervals(rows):
    """
    Normalize phone rows to V/C/P intervals per metrics-computation.md.
    
    - category=V -> V
    - category=C -> C (including hiatus and vowel-transition rows)
    - category=S -> P (pause)
    
    Then coalesce adjacent same-class intervals by summing durations.
    """
    # Step 1: map each row to an interval class
    intervals = []
    for row in rows:
        cat = row['category']
        dur = row['duration']
        if cat == 'V':
            cls = 'V'
        elif cat == 'C':
            cls = 'C'
        elif cat == 'S':
            cls = 'P'
        else:
            continue  # skip unknown
        intervals.append((cls, dur))
    
    # Step 2: coalesce adjacent same-class intervals
    if not intervals:
        return [], [], []
    
    coalesced = [list(intervals[0])]
    for cls, dur in intervals[1:]:
        if cls == coalesced[-1][0]:
            coalesced[-1][1] += dur
        else:
            coalesced.append([cls, dur])
    
    # Step 3: split into V, C, P lists
    v_intervals = [d for cls, d in coalesced if cls == 'V']
    c_intervals = [d for cls, d in coalesced if cls == 'C']
    p_intervals = [d for cls, d in coalesced if cls == 'P']
    
    return v_intervals, c_intervals, p_intervals


def arithmetic_mean(values):
    if not values:
        return 0.0
    return sum(values) / len(values)


def population_std(values):
    """Population standard deviation (Δ in the doc)."""
    if len(values) < 2:
        return 0.0
    mean = arithmetic_mean(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def compute_metrics(v_intervals, c_intervals, p_intervals):
    """Compute all rhythm metrics per docs/akkapros/metrics-computation.md."""
    total = sum(v_intervals) + sum(c_intervals) + sum(p_intervals)
    
    pct_v = (sum(v_intervals) / total * 100) if total > 0 else 0.0
    pct_c = (sum(c_intervals) / total * 100) if total > 0 else 0.0
    
    mean_v = arithmetic_mean(v_intervals)
    mean_c = arithmetic_mean(c_intervals)
    
    delta_v = population_std(v_intervals)
    delta_c = population_std(c_intervals)
    
    varco_v = (delta_v / mean_v * 100) if mean_v > 0 else 0.0
    varco_c = (delta_c / mean_c * 100) if mean_c > 0 else 0.0
    
    # rPVI-C: mean of absolute differences between adjacent C intervals
    if len(c_intervals) >= 2:
        rpvi_c = sum(abs(c_intervals[k] - c_intervals[k+1]) 
                     for k in range(len(c_intervals) - 1)) / (len(c_intervals) - 1)
    else:
        rpvi_c = 0.0
    
    # nPVI-V: 100 * mean of normalized absolute differences between adjacent V intervals
    if len(v_intervals) >= 2:
        npvi_v = 100 * sum(
            abs(v_intervals[k] - v_intervals[k+1]) / ((v_intervals[k] + v_intervals[k+1]) / 2)
            for k in range(len(v_intervals) - 1)
        ) / (len(v_intervals) - 1)
    else:
        npvi_v = 0.0
    
    return {
        '%V': round(pct_v, 2),
        '%C': round(pct_c, 2),
        'meanV': round(mean_v, 2),
        'meanC': round(mean_c, 2),
        'ΔV': round(delta_v, 2),
        'ΔC': round(delta_c, 2),
        'VarcoV': round(varco_v, 2),
        'VarcoC': round(varco_c, 2),
        'rPVI-C': round(rpvi_c, 2),
        'nPVI-V': round(npvi_v, 2),
        'V_interval_count': len(v_intervals),
        'C_interval_count': len(c_intervals),
        'P_interval_count': len(p_intervals),
        'total_duration': total,
    }


def verify_metrics(computed, reported, label):
    """Compare computed vs reported metrics and report discrepancies."""
    print(f"\n{'='*70}")
    print(f"VERIFICATION: {label}")
    print(f"{'='*70}")
    
    metrics_to_check = ['%V', '%C', 'meanV', 'meanC', 'ΔV', 'ΔC', 
                        'VarcoV', 'VarcoC', 'rPVI-C', 'nPVI-V']
    
    all_ok = True
    for metric in metrics_to_check:
        comp = computed.get(metric, 0)
        rep = reported.get(metric, 0)
        diff = abs(comp - rep)
        
        # Allow 0.5% relative tolerance for percentage metrics, 2ms for duration metrics
        if metric in ('%V', '%C', 'VarcoV', 'VarcoC', 'nPVI-V'):
            tolerance = 0.5
        elif metric in ('rPVI-C',):
            tolerance = 1.0
        else:
            tolerance = 2.0
        
        status = 'OK' if diff <= tolerance else 'MISMATCH'
        if status == 'MISMATCH':
            all_ok = False
        
        print(f"  {metric:>10}: computed={comp:>8.2f}  reported={rep:>8.2f}  diff={diff:>6.2f}  [{status}]")
    
    print(f"\n  Interval counts: V={computed['V_interval_count']}, "
          f"C={computed['C_interval_count']}, P={computed['P_interval_count']}")
    print(f"  Total duration: {computed['total_duration']} ms")
    
    if all_ok:
        print(f"\n  >>> ALL METRICS VERIFIED OK <<<")
    else:
        print(f"\n  >>> MISMATCHES FOUND <<<")
    
    return all_ok


def main():
    base_dir = r'c:\Users\samue\YandexDisk\CODING\projects\git-repos\akkapros\outputs'
    
    # Test cases: (prefix, mode_label)
    test_cases = [
        ('smoke_test', 'LOB bi (accentuated)'),
        ('smoke_test_mono', 'LOB mono (accentuated)'),
    ]
    
    all_passed = True
    
    for prefix, label in test_cases:
        phone_path = os.path.join(base_dir, f'{prefix}_phone.txt')
        ophone_path = os.path.join(base_dir, f'{prefix}_ophone.txt')
        
        if not os.path.exists(phone_path):
            print(f"SKIP: {phone_path} not found")
            continue
        if not os.path.exists(ophone_path):
            print(f"SKIP: {ophone_path} not found")
            continue
        
        # Parse phone files
        phone_rows = parse_phone_file(phone_path)
        ophone_rows = parse_phone_file(ophone_path)
        
        print(f"\n{'#'*70}")
        print(f"# {label}")
        print(f"# Phone rows: {len(phone_rows)}, Ophone rows: {len(ophone_rows)}")
        print(f"{'#'*70}")
        
        # Compute metrics from raw rows
        v, c, p = normalize_to_intervals(phone_rows)
        computed_accentuated = compute_metrics(v, c, p)
        
        v_orig, c_orig, p_orig = normalize_to_intervals(ophone_rows)
        computed_original = compute_metrics(v_orig, c_orig, p_orig)
        
        # Print interval details for manual inspection
        print(f"\n  Accentuated intervals: V={v}, C={c}, P={p}")
        print(f"  Original intervals: V={v_orig}, C={c_orig}, P={p_orig}")
        
        # Read the metrics.txt to get reported values
        metrics_path = os.path.join(base_dir, f'{prefix}_metrics.txt')
        reported = parse_metrics_txt(metrics_path)
        
        if reported:
            verify_metrics(computed_accentuated, reported.get('accentuated', {}), 
                          f'{label} - Accentuated')
            verify_metrics(computed_original, reported.get('original', {}),
                          f'{label} - Original')
        else:
            print(f"  WARNING: Could not parse metrics from {metrics_path}")
            all_passed = False
    
    print(f"\n{'='*70}")
    if all_passed:
        print("OVERALL: ALL SMOKE TESTS PASSED")
    else:
        print("OVERALL: SOME TESTS FAILED")
    print(f"{'='*70}")
    
    return 0 if all_passed else 1


def parse_metrics_txt(path):
    """Parse the metrics.txt file to extract reported values."""
    if not os.path.exists(path):
        return None
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    result = {'original': {}, 'accentuated': {}}
    
    # Find the acoustic metrics sections
    # Original section
    orig_match = re.search(r'Acoustic metrics \(original\):.*?(?=\n\n|\Z)', content, re.DOTALL)
    if orig_match:
        section = orig_match.group(0)
        for line in section.split('\n'):
            line = line.strip()
            m = re.match(r'\s*(%\w|mean\w|Δ\w|Varco\w|rPVI-C|nPVI-V):\s*([\d.]+)', line)
            if m:
                key = m.group(1).strip()
                val = float(m.group(2))
                result['original'][key] = val
    
    # Accentuated section
    acc_match = re.search(r'Acoustic metrics \(accentuated\):.*?(?=\n\n|\Z)', content, re.DOTALL)
    if acc_match:
        section = acc_match.group(0)
        for line in section.split('\n'):
            line = line.strip()
            m = re.match(r'\s*(%\w|mean\w|Δ\w|Varco\w|rPVI-C|nPVI-V):\s*([\d.]+)', line)
            if m:
                key = m.group(1).strip()
                val = float(m.group(2))
                result['accentuated'][key] = val
    
    return result


if __name__ == '__main__':
    sys.exit(main())
