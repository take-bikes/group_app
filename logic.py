import random
import itertools
import copy
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

        # --- 重み設定（ここを調整） ---
        # 過去の重複は絶対に避けたいので超特大ペナルティ
        self.WEIGHT_HISTORY = 10000    
        # 女性1人はかわいそうなので大きめのペナルティ
        self.WEIGHT_SOLE_FEMALE = 500  
        # 学年被りは、まぁ仕方ないこともあるので小さめ
        self.WEIGHT_SAME_GRADE = 50    

    def _get_pair_key(self, p1_name, p2_name):
        return tuple(sorted((p1_name, p2_name)))

    def _calculate_cost(self, groups):
        """
        グループ分けのコスト計算（低いほど良い）
        """
        total_cost = 0
        
        for group in groups:
            # メンバー数リスト
            names = [p['name'] for p in group]
            grades = [p['grade'] for p in group]
            genders = [p['gender'] for p in group]

            # --- 1. 過去の履歴チェック（最重要） ---
            for p1_name, p2_name in itertools.combinations(names, 2):
                pair_key = self._get_pair_key(p1_name, p2_name)
                hist_count = self.pair_history[pair_key]
                if hist_count > 0:
                    # 2回目なら10000点、3回目なら40000点...と激増させる
                    total_cost += (hist_count ** 2) * self.WEIGHT_HISTORY

            # --- 2. 女性1人ぼっちチェック ---
            # '女', 'F', 'woman' などが含まれるか
            female_count = sum(1 for g in genders if str(g).upper() in ['女', 'F', 'FEMALE', 'WOMAN'])
            if female_count == 1:
                total_cost += self.WEIGHT_SOLE_FEMALE

            # --- 3. 学年の分散チェック ---
            # 同じ学年のペアの数を数える
            for g1, g2 in itertools.combinations(grades, 2):
                if g1 == g2:
                    total_cost += self.WEIGHT_SAME_GRADE

        return total_cost

    def get_score_details(self, groups):
        """
        詳細なスコア内訳を計算して返す
        """
        details = {
            'history': 0,
            'gender': 0,
            'grade': 0,
            'total': 0
        }

        for group in groups:
            names = [p['name'] for p in group]
            grades = [p['grade'] for p in group]
            genders = [p['gender'] for p in group]

            # 1. 履歴
            for p1_name, p2_name in itertools.combinations(names, 2):
                pair_key = self._get_pair_key(p1_name, p2_name)
                hist_count = self.pair_history[pair_key]
                if hist_count > 0:
                    cost = (hist_count ** 2) * self.WEIGHT_HISTORY
                    details['history'] += cost
                    details['total'] += cost

            # 2. 性別
            female_count = sum(1 for g in genders if str(g).upper() in ['女', 'F', 'FEMALE', 'WOMAN'])
            if female_count == 1:
                cost = self.WEIGHT_SOLE_FEMALE
                details['gender'] += cost
                details['total'] += cost

            # 3. 学年
            for g1, g2 in itertools.combinations(grades, 2):
                if g1 == g2:
                    cost = self.WEIGHT_SAME_GRADE
                    details['grade'] += cost
                    details['total'] += cost
        
        return details

    def _update_history(self, groups):
        """確定したグループ分けを履歴に記録"""
        for group in groups:
            names = [p['name'] for p in group]
            for p1, p2 in itertools.combinations(names, 2):
                pair = self._get_pair_key(p1, p2)
                self.pair_history[pair] += 1

    def make_groups(self, num_groups, num_days, attempts=10):
        """
        attempts: ここでは「ランダム初期化の回数」
        optimize_steps: その後の「交換改善」の回数
        """
        schedule = [] 
        optimize_steps = 2000 # 1回の生成につき何回「入れ替え」を試すか

        # 今回のセッション内での履歴（過去のDB履歴は含まない）
        session_pair_history = defaultdict(int)

        for day in range(1, num_days + 1):
            best_groups = None
            min_cost = float('inf')

            # --- 1. 多点スタート（局所解回避のため数回最初からやり直す） ---
            for _ in range(attempts):
                # A. ランダム初期解の生成
                shuffled = self.participants[:]
                random.shuffle(shuffled)
                
                current_groups = []
                k, m = divmod(len(shuffled), num_groups)
                start_idx = 0
                for i in range(num_groups):
                    group_size = k + 1 if i < m else k
                    current_groups.append(shuffled[start_idx : start_idx + group_size])
                    start_idx += group_size

                current_cost = self._calculate_cost(current_groups)

                # B. 山登り法（改善ループ）
                # ランダムに2人選んで入れ替え、スコアが良くなれば採用
                for _ in range(optimize_steps):
                    if current_cost == 0:
                        break # 完璧なら終了

                    # グループを2つ選ぶ（g1_idx != g2_idx）
                    g1_idx, g2_idx = random.sample(range(num_groups), 2)
                    
                    # それぞれのグループからメンバーを1人選ぶ
                    # (空グループ対策: 万が一要素がない場合はスキップ)
                    if not current_groups[g1_idx] or not current_groups[g2_idx]:
                        continue

                    p1_idx = random.randrange(len(current_groups[g1_idx]))
                    p2_idx = random.randrange(len(current_groups[g2_idx]))

                    # --- スワップ実行 ---
                    # 一時的に入れ替えてみる
                    p1 = current_groups[g1_idx][p1_idx]
                    p2 = current_groups[g2_idx][p2_idx]
                    
                    current_groups[g1_idx][p1_idx] = p2
                    current_groups[g2_idx][p2_idx] = p1

                    # 新コスト計算
                    # (全グループ計算しなおすと重いので、影響ある2グループだけ計算すれば高速だが、
                    #  コードの単純化のため全体計算を行う。50人程度なら十分高速)
                    new_cost = self._calculate_cost(current_groups)

                    if new_cost < current_cost:
                        # 改善したので採用（そのまま）
                        current_cost = new_cost
                    else:
                        # 改悪または変化なしなので戻す（Revert）
                        current_groups[g1_idx][p1_idx] = p1
                        current_groups[g2_idx][p2_idx] = p2

                # この試行の結果が、今までのベストなら記録
                if current_cost < min_cost:
                    min_cost = current_cost
                    # 深いコピーをとっておく（参照渡し対策）
                    best_groups = copy.deepcopy(current_groups)
                
                if min_cost == 0:
                    break

            # 履歴更新（DB保存用・次回の計算用）
            self._update_history(best_groups)
            
            # 詳細スコア計算
            details = self.get_score_details(best_groups)

            # --- 今回のリクエスト対応: セッション内のみの重複数を計算 ---
            session_dupes = 0
            for group in best_groups:
                names = [p['name'] for p in group]
                for p1, p2 in itertools.combinations(names, 2):
                    pair = self._get_pair_key(p1, p2)
                    if session_pair_history[pair] > 0:
                        session_dupes += 1
            
            # セッション履歴も更新
            for group in best_groups:
                names = [p['name'] for p in group]
                for p1, p2 in itertools.combinations(names, 2):
                    pair = self._get_pair_key(p1, p2)
                    session_pair_history[pair] += 1
            
            # detailsに追加
            details['duplicate_count'] = session_dupes

            # 結果出力用に整形
            display_groups = []
            for g in best_groups:
                display_groups.append([
                    {'name': p['name'], 'grade': p['grade'], 'gender': p['gender']}
                    for p in g
                ])

            schedule.append({
                "day": day,
                "groups": display_groups,
                "cost": min_cost,
                "details": details 
            })

        return schedule