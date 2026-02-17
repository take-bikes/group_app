import random
import itertools
from collections import defaultdict

class GroupOptimizer:
    def __init__(self, participants):
        """
        participants: 辞書のリスト
        例: [{'name': 'Aさん', 'grade': '1', 'gender': 'F'}, ...]
        """
        self.participants = participants
        # 履歴辞書: キーは (名前1, 名前2)
        self.pair_history = defaultdict(int)

    def _get_pair_key(self, p1_name, p2_name):
        """名前だけでキーを作る"""
        return tuple(sorted((p1_name, p2_name)))

    def _calculate_cost(self, groups):
        """
        グループ分けの良し悪しを計算する（点数が低いほど良い）
        """
        total_cost = 0
        
        # 重み付け設定（これを調整して優先度を変えます）
        WEIGHT_HISTORY = 100    # 過去に会った人との重複
        WEIGHT_SOLE_FEMALE = 50 # 女性が1人だけのグループ（避けるべき）
        WEIGHT_SAME_GRADE = 10  # 同じ学年が被る（分散させたい）

        for group in groups:
            # --- 1. 学年の分散チェック ---
            # グループ内のペアを見て、同じ学年ならペナルティ
            for p1, p2 in itertools.combinations(group, 2):
                if p1['grade'] == p2['grade']:
                    total_cost += WEIGHT_SAME_GRADE

            # --- 2. 女性1人ぼっちチェック ---
            # グループ内の女性の数をカウント
            # (入力が "女", "F", "Female" など揺れがあってもいいように判定)
            females = [p for p in group if p['gender'] in ['女', 'F', 'Female', 'woman']]
            if len(females) == 1:
                total_cost += WEIGHT_SOLE_FEMALE

            # --- 3. 過去の履歴チェック ---
            for p1, p2 in itertools.combinations(group, 2):
                pair_key = self._get_pair_key(p1['name'], p2['name'])
                # 過去に会った回数の2乗をペナルティに
                hist_count = self.pair_history[pair_key]
                if hist_count > 0:
                    total_cost += (hist_count ** 2) * WEIGHT_HISTORY

        return total_cost

    def _update_history(self, groups):
        """確定したグループ分けを履歴に記録"""
        for group in groups:
            for p1, p2 in itertools.combinations(group, 2):
                pair = self._get_pair_key(p1['name'], p2['name'])
                self.pair_history[pair] += 1

    def make_groups(self, num_groups, num_days, attempts=2000):
        schedule = [] 

        for day in range(1, num_days + 1):
            best_groups = None
            min_cost = float('inf')

            for _ in range(attempts):
                # シャッフル
                shuffled = self.participants[:]
                random.shuffle(shuffled)

                # 分割処理
                current_groups = []
                k, m = divmod(len(shuffled), num_groups)
                start_idx = 0
                for i in range(num_groups):
                    group_size = k + 1 if i < m else k
                    current_groups.append(shuffled[start_idx : start_idx + group_size])
                    start_idx += group_size

                # コスト計算
                cost = self._calculate_cost(current_groups)

                if cost < min_cost:
                    min_cost = cost
                    best_groups = current_groups
                
                # ペナルティ0なら即決
                if cost == 0:
                    break

            # 履歴更新
            self._update_history(best_groups)
            
            # 結果出力用に「名前だけのリスト」に変換しておく
            display_groups = []
            for g in best_groups:
                # 画面表示用にオブジェクトのまま返す (修正)
                display_groups.append([
                    {'name': p['name'], 'grade': p['grade'], 'gender': p['gender']}
                    for p in g
                ])

            schedule.append({
                "day": day,
                "groups": display_groups,
                "cost": min_cost
            })

        return schedule