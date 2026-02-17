import random
import itertools
from collections import defaultdict

class GroupOptimizer:
    def __init__(self, participants):
        """
        participants: 参加者のリスト (例: ["Aさん", "Bさん", ...])
        """
        self.participants = participants
        # 誰と誰が何回一緒になったかを記録する辞書
        # キーは (名前1, 名前2) のタプル (名前はアルファベット順にソートして格納)
        self.pair_history = defaultdict(int)

    def _get_pair_key(self, p1, p2):
        """ペアのキーを正規化して返す（AとB、BとAを同じものとして扱うため）"""
        return tuple(sorted((p1, p2)))

    def _calculate_cost(self, groups):
        """
        今回のグループ分けで、過去に重複したペアがどれくらい含まれるかを計算する
        コストが高い＝重複が多い（悪い組み合わせ）
        """
        cost = 0
        for group in groups:
            # グループ内の全ての2人組（ペア）を作成
            for p1, p2 in itertools.combinations(group, 2):
                pair = self._get_pair_key(p1, p2)
                # 過去に一緒になった回数をコストとして加算
                # 2乗することで、同じ人と3回以上一緒になることを強く避ける
                cost += (self.pair_history[pair]) ** 2
        return cost

    def _update_history(self, groups):
        """確定したグループ分けを履歴に記録する"""
        for group in groups:
            for p1, p2 in itertools.combinations(group, 2):
                pair = self._get_pair_key(p1, p2)
                self.pair_history[pair] += 1

    def make_groups(self, num_groups, num_days, attempts=1000):
        """
        メインの処理
        num_groups: 分けたいグループの数
        num_days: 日数
        attempts: 1日あたり何回シミュレーションして最適解を探すか（多いほど精度が上がる）
        """
        schedule = [] # 全日程の結果を格納するリスト

        # 1グループあたりの基本人数（あまりが出る場合もある）
        # ※ここでは簡易的にリストを分割するロジックを使用
        
        for day in range(1, num_days + 1):
            best_groups = None
            min_cost = float('inf') # 無限大で初期化

            # 指定回数だけランダムに試行錯誤する
            for _ in range(attempts):
                # 参加者をシャッフル
                shuffled = self.participants[:] # コピーを作成
                random.shuffle(shuffled)

                # リストを num_groups 個に分割する
                # 例: 10人を3グループ -> [4人, 3人, 3人] のように分割
                current_groups = []
                k, m = divmod(len(shuffled), num_groups)
                # k = 基本人数, m = 余りの人数（1人多くなるグループ数）
                
                start_idx = 0
                for i in range(num_groups):
                    # 余りがあるうちは人数を+1する
                    group_size = k + 1 if i < m else k
                    current_groups.append(shuffled[start_idx : start_idx + group_size])
                    start_idx += group_size

                # コスト計算（重複チェック）
                cost = self._calculate_cost(current_groups)

                # これまでで一番マシな組み合わせなら保持する
                if cost < min_cost:
                    min_cost = cost
                    best_groups = current_groups
                
                # コスト0（重複なし）が見つかったら、試行を打ち切って即採用（高速化）
                if cost == 0:
                    break

            # その日のベストな組み合わせを履歴に反映
            self._update_history(best_groups)
            
            # 結果リストに追加
            schedule.append({
                "day": day,
                "groups": best_groups,
                "cost": min_cost # デバッグ用：この日の重複度合い
            })

        return schedule

# --- 動作確認用のコード（このファイルを直接実行した時だけ動く） ---
if __name__ == "__main__":
    # テストデータ：15人の参加者
    names = [f"参加者{i}" for i in range(1, 16)]
    
    # グループ分け実行（15人を4グループに分ける、3日間）
    optimizer = GroupOptimizer(names)
    result = optimizer.make_groups(num_groups=4, num_days=3)

    # 結果表示
    for day_info in result:
        print(f"--- {day_info['day']}日目 (重複コスト: {day_info['cost']}) ---")
        for i, group in enumerate(day_info['groups'], 1):
            print(f"  グループ{i}: {', '.join(group)}")
