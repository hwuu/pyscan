"""
构建 ground_truth.json 从所有 metadata.yaml 文件
"""

import yaml
import json
from pathlib import Path


def build_ground_truth():
    """从所有 positive/metadata.yaml 收集 bug 信息"""

    benchmarks_dir = Path(__file__).parent
    categories_dir = benchmarks_dir / "categories"

    all_bugs = []
    stats = {
        'by_category': {},
        'by_severity': {'high': 0, 'medium': 0, 'low': 0},
        'by_difficulty': {'easy': 0, 'medium': 0, 'hard': 0}
    }

    # 遍历所有 positive/metadata.yaml
    for meta_file in categories_dir.rglob("positive/metadata.yaml"):
        print(f"Processing: {meta_file}")

        with open(meta_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        bugs = data.get('bugs', [])
        for bug in bugs:
            # 添加相对路径信息
            relative_dir = meta_file.parent.relative_to(categories_dir)
            bug['relative_path'] = str(relative_dir / bug['file'])

            all_bugs.append(bug)

            # 更新统计
            category = bug.get('category', 'unknown')
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1

            severity = bug.get('severity', 'medium')
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1

            difficulty = bug.get('difficulty', 'medium')
            stats['by_difficulty'][difficulty] = stats['by_difficulty'].get(difficulty, 0) + 1

    # 构建 ground_truth
    ground_truth = {
        'version': '0.1',
        'created_date': '2025-10-19',
        'total_bugs': len(all_bugs),
        'statistics': stats,
        'bugs': all_bugs
    }

    # 保存到 ground_truth.json
    output_file = benchmarks_dir / "ground_truth.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(ground_truth, f, indent=2, ensure_ascii=False)

    print(f"\nGround truth generated: {output_file}")
    print(f"Total bugs: {len(all_bugs)}")
    print(f"By category: {stats['by_category']}")
    print(f"By severity: {stats['by_severity']}")
    print(f"By difficulty: {stats['by_difficulty']}")


if __name__ == '__main__':
    build_ground_truth()
