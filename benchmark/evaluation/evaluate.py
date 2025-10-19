"""
PyScan Benchmark 评估脚本

评估 PyScan 在 benchmark 测试集上的表现，计算 Precision、Recall 和 F1 Score
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple


class BenchmarkEvaluator:
    """Benchmark 评估器"""

    def __init__(self, ground_truth_path: str, report_path: str):
        """
        初始化评估器

        Args:
            ground_truth_path: ground_truth.json 文件路径
            report_path: PyScan 生成的 report.json 文件路径
        """
        self.ground_truth = self._load_json(ground_truth_path)
        self.pyscan_report = self._load_json(report_path)

        self.gt_bugs = self.ground_truth.get('bugs', [])
        self.detected_bugs = self.pyscan_report.get('bugs', [])

    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """加载 JSON 文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def evaluate(self) -> Dict[str, Any]:
        """
        评估 PyScan 检测结果

        Returns:
            包含评估指标的字典
        """
        # 匹配 bugs
        tp, fp, fn, matches = self._match_bugs()

        # 计算指标
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        # 按类别分析
        by_category = self._analyze_by_category(matches)

        # 按严重程度分析
        by_severity = self._analyze_by_severity(matches)

        # 按难度分析
        by_difficulty = self._analyze_by_difficulty(matches)

        # False positives 详情
        fp_details = self._get_false_positives(matches)

        # False negatives 详情
        fn_details = self._get_false_negatives(matches)

        return {
            'summary': {
                'precision': round(precision, 4),
                'recall': round(recall, 4),
                'f1_score': round(f1, 4),
                'true_positives': tp,
                'false_positives': fp,
                'false_negatives': fn,
                'total_ground_truth_bugs': len(self.gt_bugs),
                'total_detected_bugs': len(self.detected_bugs)
            },
            'by_category': by_category,
            'by_severity': by_severity,
            'by_difficulty': by_difficulty,
            'false_positives': fp_details,
            'false_negatives': fn_details,
            'matches': matches
        }

    def _match_bugs(self) -> Tuple[int, int, int, List[Dict[str, Any]]]:
        """
        匹配 ground truth 和检测到的 bugs

        Returns:
            (true_positives, false_positives, false_negatives, matches)
        """
        matches = []
        matched_gt_ids = set()
        matched_detected_ids = set()

        # 尝试匹配每个检测到的 bug
        for i, detected_bug in enumerate(self.detected_bugs):
            best_match = None
            best_match_score = 0

            for j, gt_bug in enumerate(self.gt_bugs):
                if gt_bug['id'] in matched_gt_ids:
                    continue

                score = self._bugs_similarity(gt_bug, detected_bug)
                if score > best_match_score:
                    best_match_score = score
                    best_match = j

            # 如果匹配度足够高，认为是匹配成功
            if best_match is not None and best_match_score >= 0.7:
                gt_bug = self.gt_bugs[best_match]
                matches.append({
                    'type': 'TP',
                    'gt_bug': gt_bug,
                    'detected_bug': detected_bug,
                    'similarity': best_match_score
                })
                matched_gt_ids.add(gt_bug['id'])
                matched_detected_ids.add(i)
            else:
                # False Positive
                matches.append({
                    'type': 'FP',
                    'detected_bug': detected_bug
                })

        # False Negatives: ground truth 中未被匹配的 bugs
        for gt_bug in self.gt_bugs:
            if gt_bug['id'] not in matched_gt_ids:
                matches.append({
                    'type': 'FN',
                    'gt_bug': gt_bug
                })

        tp = sum(1 for m in matches if m['type'] == 'TP')
        fp = sum(1 for m in matches if m['type'] == 'FP')
        fn = sum(1 for m in matches if m['type'] == 'FN')

        return tp, fp, fn, matches

    def _bugs_similarity(self, gt_bug: Dict[str, Any], detected_bug: Dict[str, Any]) -> float:
        """
        计算两个 bug 的相似度

        匹配规则:
        1. 文件路径必须一致 (或部分匹配)
        2. 函数名必须一致
        3. 行号在合理范围内 (±5 行)
        4. Bug 类型相似 (可选)

        Returns:
            相似度分数 (0.0 - 1.0)
        """
        score = 0.0

        # 1. 文件路径匹配 (40%)
        gt_file = gt_bug.get('file', '')
        detected_file = detected_bug.get('file_path', '')

        if gt_file in detected_file or detected_file.endswith(gt_file):
            score += 0.4

        # 2. 函数名匹配 (40%)
        if gt_bug.get('function') == detected_bug.get('function_name'):
            score += 0.4

        # 3. 行号匹配 (20%)
        gt_line = gt_bug.get('location', {}).get('start_line', 0)
        detected_line = detected_bug.get('start_line', 0)

        # 注意: detected_line 是相对于函数的，需要转换为绝对行号
        # 简化处理：检查是否在合理范围内
        line_diff = abs(gt_line - detected_line)
        if line_diff <= 5:
            score += 0.2 * (1 - line_diff / 5)

        return score

    def _analyze_by_category(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """按类别分析"""
        by_category = {}

        for match in matches:
            if match['type'] in ['TP', 'FN']:
                bug = match.get('gt_bug')
            else:
                continue  # FP 没有 category 信息

            category = bug.get('category', 'unknown')
            if category not in by_category:
                by_category[category] = {'TP': 0, 'FP': 0, 'FN': 0}

            by_category[category][match['type']] += 1

        # 计算每个类别的指标
        for category, counts in by_category.items():
            tp = counts['TP']
            fp = counts['FP']
            fn = counts['FN']

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

            counts.update({
                'precision': round(precision, 4),
                'recall': round(recall, 4),
                'f1_score': round(f1, 4)
            })

        return by_category

    def _analyze_by_severity(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """按严重程度分析"""
        by_severity = {}

        for match in matches:
            if match['type'] in ['TP', 'FN']:
                bug = match.get('gt_bug')
            else:
                continue

            severity = bug.get('severity', 'medium')
            if severity not in by_severity:
                by_severity[severity] = {'TP': 0, 'FN': 0}

            by_severity[severity][match['type']] += 1

        # 计算召回率
        for severity, counts in by_severity.items():
            tp = counts['TP']
            fn = counts['FN']
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            counts['recall'] = round(recall, 4)

        return by_severity

    def _analyze_by_difficulty(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """按难度分析"""
        by_difficulty = {}

        for match in matches:
            if match['type'] in ['TP', 'FN']:
                bug = match.get('gt_bug')
            else:
                continue

            difficulty = bug.get('difficulty', 'medium')
            if difficulty not in by_difficulty:
                by_difficulty[difficulty] = {'TP': 0, 'FN': 0}

            by_difficulty[difficulty][match['type']] += 1

        # 计算召回率
        for difficulty, counts in by_difficulty.items():
            tp = counts['TP']
            fn = counts['FN']
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            counts['recall'] = round(recall, 4)

        return by_difficulty

    def _get_false_positives(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """获取 False Positives 详情"""
        fps = []
        for match in matches:
            if match['type'] == 'FP':
                bug = match['detected_bug']
                fps.append({
                    'bug_id': bug.get('bug_id'),
                    'file': bug.get('file_path'),
                    'function': bug.get('function_name'),
                    'line': bug.get('start_line'),
                    'type': bug.get('type'),
                    'description': bug.get('description')
                })
        return fps

    def _get_false_negatives(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """获取 False Negatives 详情"""
        fns = []
        for match in matches:
            if match['type'] == 'FN':
                bug = match['gt_bug']
                fns.append({
                    'bug_id': bug.get('id'),
                    'file': bug.get('file'),
                    'function': bug.get('function'),
                    'line': bug.get('location', {}).get('start_line'),
                    'type': bug.get('type'),
                    'description': bug.get('description'),
                    'difficulty': bug.get('difficulty')
                })
        return fns


def main():
    parser = argparse.ArgumentParser(description='Evaluate PyScan on benchmark')
    parser.add_argument('--ground-truth', '-g', required=True, help='Path to ground_truth.json')
    parser.add_argument('--report', '-r', required=True, help='Path to PyScan report.json')
    parser.add_argument('--output', '-o', default='evaluation_report.json', help='Output file path')

    args = parser.parse_args()

    # 运行评估
    evaluator = BenchmarkEvaluator(args.ground_truth, args.report)
    results = evaluator.evaluate()

    # 保存结果
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # 打印摘要
    print("=" * 80)
    print("PyScan Benchmark 评估结果")
    print("=" * 80)
    print(f"\nPrecision: {results['summary']['precision']:.2%}")
    print(f"Recall:    {results['summary']['recall']:.2%}")
    print(f"F1 Score:  {results['summary']['f1_score']:.4f}")
    print(f"\nTrue Positives:  {results['summary']['true_positives']}")
    print(f"False Positives: {results['summary']['false_positives']}")
    print(f"False Negatives: {results['summary']['false_negatives']}")

    print(f"\n详细报告已保存到: {args.output}")


if __name__ == '__main__':
    main()
