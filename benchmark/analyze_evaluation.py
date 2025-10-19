#!/usr/bin/env python3
"""
分析 PyScan benchmark 评估结果
对比 Ground Truth 和检测结果，计算 Precision/Recall/F1
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


def load_ground_truth(gt_path: str) -> Dict:
    """加载 ground truth"""
    with open(gt_path, encoding='utf-8') as f:
        return json.load(f)


def load_report(report_path: str) -> Dict:
    """加载检测报告"""
    with open(report_path, encoding='utf-8') as f:
        return json.load(f)


def match_bugs(gt_bugs: List[Dict], detected_bugs: List[Dict]) -> Tuple[List, List, List]:
    """
    匹配 ground truth 和检测结果

    匹配策略:
    1. 优先按 bug_id 匹配（如果检测结果有提供）
    2. 按文件名 + 函数名 + 位置匹配
    3. 按文件名 + 函数名匹配（位置可能略有偏差）

    返回:
        (true_positives, false_positives, false_negatives)
    """
    # 构建 ground truth 索引
    gt_by_file_func = defaultdict(list)
    gt_by_id = {}

    for gt_bug in gt_bugs:
        file_name = gt_bug.get('file', '')
        func_name = gt_bug.get('function', '')
        bug_id = gt_bug.get('id', '')

        key = (file_name, func_name)
        gt_by_file_func[key].append(gt_bug)

        if bug_id:
            gt_by_id[bug_id] = gt_bug

    # 匹配检测结果
    true_positives = []
    false_positives = []
    matched_gt_ids = set()

    for detected_bug in detected_bugs:
        # 从 file_path 中提取文件名
        file_path = detected_bug.get('file_path', '')
        file_name = Path(file_path).name if file_path else ''
        func_name = detected_bug.get('function_name', '')

        # 尝试匹配
        matched = False

        # 策略 1: 按文件名 + 函数名匹配
        key = (file_name, func_name)
        if key in gt_by_file_func:
            candidate_bugs = gt_by_file_func[key]

            # 在同一函数中，可能有多个 bugs，尝试按位置匹配
            detected_line = detected_bug.get('start_line', 0)

            for gt_bug in candidate_bugs:
                gt_id = gt_bug.get('id', '')
                if gt_id in matched_gt_ids:
                    continue  # 已匹配过

                gt_start = gt_bug.get('location', {}).get('start_line', 0)
                gt_end = gt_bug.get('location', {}).get('end_line', 0)

                # 位置匹配（允许 ±2 行的误差）
                if gt_start - 2 <= detected_line <= gt_end + 2:
                    true_positives.append({
                        'gt_bug': gt_bug,
                        'detected_bug': detected_bug,
                        'match_type': 'file_func_line'
                    })
                    matched_gt_ids.add(gt_id)
                    matched = True
                    break

            # 如果位置匹配失败，但函数匹配成功，也算匹配（宽松策略）
            if not matched and candidate_bugs:
                for gt_bug in candidate_bugs:
                    gt_id = gt_bug.get('id', '')
                    if gt_id not in matched_gt_ids:
                        true_positives.append({
                            'gt_bug': gt_bug,
                            'detected_bug': detected_bug,
                            'match_type': 'file_func'
                        })
                        matched_gt_ids.add(gt_id)
                        matched = True
                        break

        if not matched:
            false_positives.append(detected_bug)

    # 未匹配的 ground truth bugs 即为漏报
    false_negatives = [
        gt_bug for gt_bug in gt_bugs
        if gt_bug.get('id', '') not in matched_gt_ids
    ]

    return true_positives, false_positives, false_negatives


def calculate_metrics(tp_count: int, fp_count: int, fn_count: int) -> Dict:
    """计算评估指标"""
    precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0
    recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'true_positives': tp_count,
        'false_positives': fp_count,
        'false_negatives': fn_count
    }


def analyze_by_category(true_positives: List, false_positives: List,
                        false_negatives: List, gt_bugs: List) -> Dict:
    """按类别分析"""
    category_stats = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0, 'total_gt': 0})

    # 统计 TP
    for tp in true_positives:
        category = tp['gt_bug'].get('category', 'unknown')
        category_stats[category]['tp'] += 1

    # 统计 FP
    for fp in false_positives:
        category = fp.get('category', 'unknown')
        category_stats[category]['fp'] += 1

    # 统计 FN
    for fn in false_negatives:
        category = fn.get('category', 'unknown')
        category_stats[category]['fn'] += 1

    # 统计 Ground Truth 总数
    for gt_bug in gt_bugs:
        category = gt_bug.get('category', 'unknown')
        category_stats[category]['total_gt'] += 1

    # 计算每个类别的指标
    results = {}
    for category, stats in category_stats.items():
        results[category] = {
            **stats,
            **calculate_metrics(stats['tp'], stats['fp'], stats['fn'])
        }

    return results


def analyze_by_difficulty(true_positives: List, false_negatives: List) -> Dict:
    """按难度分析检测率"""
    difficulty_stats = defaultdict(lambda: {'detected': 0, 'total': 0})

    # TP 中的难度分布
    for tp in true_positives:
        difficulty = tp['gt_bug'].get('difficulty', 'unknown')
        difficulty_stats[difficulty]['detected'] += 1
        difficulty_stats[difficulty]['total'] += 1

    # FN 中的难度分布
    for fn in false_negatives:
        difficulty = fn.get('difficulty', 'unknown')
        difficulty_stats[difficulty]['total'] += 1

    # 计算检测率
    results = {}
    for difficulty, stats in difficulty_stats.items():
        detection_rate = stats['detected'] / stats['total'] if stats['total'] > 0 else 0
        results[difficulty] = {
            **stats,
            'detection_rate': detection_rate
        }

    return results


def main():
    # 路径配置
    gt_path = 'benchmark/ground_truth.json'
    report_path = 'benchmark_evaluation_full.json'

    print("=" * 70)
    print("PyScan Benchmark 详细评估分析")
    print("=" * 70)

    # 加载数据
    print("\n[1/5] 加载数据...")
    gt = load_ground_truth(gt_path)
    report = load_report(report_path)

    gt_bugs = gt['bugs']
    detected_bugs = report['bugs']

    print(f"  Ground Truth: {len(gt_bugs)} bugs")
    print(f"  检测结果: {len(detected_bugs)} bugs")

    # 匹配 bugs
    print("\n[2/5] 匹配 bugs...")
    true_positives, false_positives, false_negatives = match_bugs(gt_bugs, detected_bugs)

    print(f"  True Positives: {len(true_positives)}")
    print(f"  False Positives: {len(false_positives)}")
    print(f"  False Negatives: {len(false_negatives)}")

    # 计算整体指标
    print("\n[3/5] 计算整体指标...")
    overall_metrics = calculate_metrics(
        len(true_positives),
        len(false_positives),
        len(false_negatives)
    )

    print(f"\n【整体指标】")
    print(f"  Precision: {overall_metrics['precision']:.2%}")
    print(f"  Recall:    {overall_metrics['recall']:.2%}")
    print(f"  F1 Score:  {overall_metrics['f1']:.2%}")

    # 按类别分析
    print("\n[4/5] 按类别分析...")
    category_results = analyze_by_category(
        true_positives, false_positives, false_negatives, gt_bugs
    )

    print(f"\n【按类别统计】")
    print(f"{'类别':<25} {'TP':>4} {'FP':>4} {'FN':>4} {'GT':>4} {'Prec':>7} {'Recall':>7} {'F1':>7}")
    print("-" * 70)
    for category in sorted(category_results.keys()):
        stats = category_results[category]
        print(f"{category:<25} {stats['tp']:>4} {stats['fp']:>4} {stats['fn']:>4} "
              f"{stats['total_gt']:>4} {stats['precision']:>6.1%} {stats['recall']:>6.1%} {stats['f1']:>6.1%}")

    # 按难度分析
    print("\n[5/5] 按难度分析...")
    difficulty_results = analyze_by_difficulty(true_positives, false_negatives)

    print(f"\n【按难度检测率】")
    print(f"{'难度':<10} {'检测到':>8} {'总数':>8} {'检测率':>10}")
    print("-" * 40)
    for difficulty in ['easy', 'medium', 'hard']:
        if difficulty in difficulty_results:
            stats = difficulty_results[difficulty]
            print(f"{difficulty:<10} {stats['detected']:>8} {stats['total']:>8} {stats['detection_rate']:>9.1%}")

    # 详细分析 FP 和 FN
    print(f"\n{'=' * 70}")
    print("详细分析")
    print("=" * 70)

    # FP 分析
    print(f"\n【False Positives 分析】({len(false_positives)} 个)")
    fp_by_file = defaultdict(list)
    for fp in false_positives:
        file_path = fp.get('file_path', 'unknown')
        file_name = Path(file_path).name if file_path != 'unknown' else 'unknown'
        fp_by_file[file_name].append(fp)

    print(f"\n按文件分布:")
    for file_name in sorted(fp_by_file.keys())[:10]:  # 显示前10个
        count = len(fp_by_file[file_name])
        print(f"  {file_name}: {count} FPs")

    if len(fp_by_file) > 10:
        print(f"  ... 还有 {len(fp_by_file) - 10} 个文件")

    # FN 分析
    print(f"\n【False Negatives 分析】({len(false_negatives)} 个)")
    fn_by_category = defaultdict(list)
    for fn in false_negatives:
        category = fn.get('category', 'unknown')
        fn_by_category[category].append(fn)

    print(f"\n按类别分布:")
    for category in sorted(fn_by_category.keys()):
        bugs = fn_by_category[category]
        print(f"  {category}: {len(bugs)} 漏报")
        for bug in bugs[:3]:  # 每个类别显示前3个
            bug_id = bug.get('id', 'N/A')
            func = bug.get('function', 'N/A')
            difficulty = bug.get('difficulty', 'N/A')
            print(f"    - {bug_id}: {func} (难度: {difficulty})")
        if len(bugs) > 3:
            print(f"    ... 还有 {len(bugs) - 3} 个")

    # 保存详细结果
    print(f"\n[保存结果] 生成详细报告...")
    detailed_results = {
        'summary': {
            'ground_truth_total': len(gt_bugs),
            'detected_total': len(detected_bugs),
            'true_positives': len(true_positives),
            'false_positives': len(false_positives),
            'false_negatives': len(false_negatives),
            **overall_metrics
        },
        'by_category': category_results,
        'by_difficulty': difficulty_results,
        'false_positives': false_positives,
        'false_negatives': false_negatives,
        'true_positives': [
            {
                'gt_id': tp['gt_bug'].get('id'),
                'gt_category': tp['gt_bug'].get('category'),
                'detected_category': tp['detected_bug'].get('category'),
                'match_type': tp['match_type']
            }
            for tp in true_positives
        ]
    }

    with open('benchmark/detailed_evaluation_results.json', 'w', encoding='utf-8') as f:
        json.dump(detailed_results, f, indent=2, ensure_ascii=False)

    print(f"  详细结果已保存到: benchmark/detailed_evaluation_results.json")

    print(f"\n{'=' * 70}")
    print("分析完成！")
    print("=" * 70)


if __name__ == '__main__':
    main()
