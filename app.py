import os
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from itertools import combinations
from logic import GroupOptimizer

app = Flask(__name__)

# --- 1. データベースの設定 ---
# アプリと同じ場所に 'group_app.db' というファイルを作って保存します
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'group_app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- 2. データベースの設計図（モデル） ---
# 「誰(p1)と誰(p2)が、何回(count)一緒になったか」を記録するテーブル
class PairHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    person1 = db.Column(db.String(50), nullable=False)
    person2 = db.Column(db.String(50), nullable=False)
    count = db.Column(db.Integer, default=0)

# アプリ起動時にデータベースファイルがなければ作成する
with app.app_context():
    db.create_all()

# --- ヘルパー関数 ---
def get_sorted_pair(name1, name2):
    """名前をアルファベット順に並び替えてタプルにする（A, Bも B, Aも同じペアとして扱うため）"""
    return tuple(sorted((name1, name2)))

def load_history_from_db():
    """DBから全履歴を読み込んで、logic.pyで使える辞書形式にする"""
    history = {}
    records = PairHistory.query.all()
    for r in records:
        history[(r.person1, r.person2)] = r.count
    return history

def save_groups_to_db(schedule):
    """計算結果のグループ分けをDBに保存（加算）する"""
    for day in schedule:
        for group in day['groups']:
            # グループ内の全ペアについて
            for p1, p2 in combinations(group, 2):
                sorted_p1, sorted_p2 = sorted((p1, p2))
                
                # DBからそのペアを探す
                record = PairHistory.query.filter_by(person1=sorted_p1, person2=sorted_p2).first()
                
                if record:
                    # 既に記録があれば回数を+1
                    record.count += 1
                else:
                    # 初めてのペアなら新規作成
                    new_record = PairHistory(person1=sorted_p1, person2=sorted_p2, count=1)
                    db.session.add(new_record)
    
    # まとめて保存実行
    db.session.commit()

# --- 3. メイン処理 ---
@app.route('/', methods=['GET', 'POST'])
def index():
    message = ""
    
    if request.method == 'POST':
        # 入力データの取得
        participants_text = request.form.get('participants')
        participants = [line.strip() for line in participants_text.splitlines() if line.strip()]

        try:
            num_groups = int(request.form.get('num_groups'))
            num_days = int(request.form.get('num_days'))
        except ValueError:
            return "数字を正しく入力してください", 400

        # ★ここが重要：DBから過去の履歴を読み込む
        existing_history = load_history_from_db()

        # オプティマイザーの準備（過去の履歴をセットする）
        optimizer = GroupOptimizer(participants)
        # logic.py の pair_history を DBのデータで上書き更新
        for pair, count in existing_history.items():
            optimizer.pair_history[pair] = count

        # 計算実行
        schedule = optimizer.make_groups(num_groups, num_days)

        # ★ここが重要：今回の結果をDBに保存する
        save_groups_to_db(schedule)
        
        message = "今回の結果をデータベースに保存しました！次回の計算ではこのペアが考慮されます。"

        return render_template('result.html', schedule=schedule, message=message)

    return render_template('index.html')

# --- 履歴リセット機能（おまけ） ---
@app.route('/reset')
def reset_db():
    # データを全削除する機能（開発中に便利）
    db.session.query(PairHistory).delete()
    db.session.commit()
    return "履歴を全てリセットしました。<a href='/'>戻る</a>"

if __name__ == '__main__':
    app.run(debug=True)