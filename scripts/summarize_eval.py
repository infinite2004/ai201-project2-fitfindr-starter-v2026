"""Combine run_eval's mechanical checks with an explicit caption text review.

Usage: python scripts/summarize_eval.py results/run_...json results/before-caption-review.json
The raw report remains unchanged. Writes a separate *_reviewed.json summary.
"""
import argparse
import json
from pathlib import Path


def summarize(report, review):
    if len(review['tries']) != 5 or [t['try'] for t in review['tries']] != list(range(1, 6)):
        raise ValueError('Supply a grounded review for all five caption trials.')
    rows = []
    for row in report['rows']:
        outcomes = [trial['passed'] for trial in row['tries']]
        if row['criterion'] == 4:
            outcomes = [passed and assessed['factually_grounded']
                        for passed, assessed in zip(outcomes, review['tries'])]
        count = sum(outcomes)
        rows.append({'criterion': row['criterion'], 'name': row['name'], 'target': row['target'],
                     'passed': outcomes, 'count': count,
                     'verdict': ('MET' if count >= row['target'] else 'MISSED') if len(outcomes) == 5 else 'INCOMPLETE'})
    return {'label': report['label'], 'caption_review': review, 'rows': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('review', type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    review = json.loads(args.review.read_text())
    result = summarize(report, review)
    result['raw_report'] = str(args.report)
    result['review_source'] = str(args.review)
    destination = args.report.with_name(args.report.stem + '_reviewed.json')
    destination.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    for row in result['rows']:
        print(f"Criterion {row['criterion']}: {row['verdict']} ({row['count']}/5; target {row['target']}/5)")
    print('Wrote', destination)


if __name__ == '__main__':
    main()
