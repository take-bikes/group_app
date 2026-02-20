import os
import json
from flask import Flask, render_template, request, redirect, url_for
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
        raw_text = request.form.get('participants')
        
        # 入力テキストを解析して辞書リストを作る
        # 入力形式: 名前,学年,性別,工具,出欠(1;1;0;1)
        participants = []
        for line in raw_text.splitlines():
            line = line.strip()
            if not line: continue
            
            parts = [p.strip() for p in line.split(',')]
            
            if not parts: continue
            
            name = parts[0]
            grade = parts[1] if len(parts) > 1 else "?"
            gender = parts[2] if len(parts) > 2 else "?"
            
            # 第4要素: 工具係判定
            is_tool = False
            if len(parts) > 3:
                is_tool = parts[3].upper() in ['TOOL', '工具', 'TRUE', 'YES', '1']

            # 第5要素: 出欠データ (例: "1;1;0;1")
            attendance = []
            if len(parts) > 4:
                attendance = [x == '1' for x in parts[4].split(';')]

            participants.append({
                'name': name,
                'grade': grade,
                'gender': gender,
                'is_tool': is_tool,
                'attendance': attendance
            })

        try:
            num_groups = int(request.form.get('num_groups'))
            num_days = int(request.form.get('num_days'))
        except ValueError:
            return "数字を正しく入力してください", 400

        # 出欠データが未設定の場合は全日参加扱い
        for p in participants:
            if not p['attendance']:
                p['attendance'] = [True] * num_days
            # 日数に合わせて調整
            while len(p['attendance']) < num_days:
                p['attendance'].append(True)

        existing_history = load_history_from_db()

        # オプティマイザーに辞書リストを渡す（出欠情報付き）
        optimizer = GroupOptimizer(participants)
        
        # 履歴データの復元
        for pair, count in existing_history.items():
            optimizer.pair_history[pair] = count

        # カップルペアの偽装履歴を注入（同じグループを回避するため）
        couples_json = request.form.get('couples', '[]')
        couples = json.loads(couples_json)
        for couple in couples:
            name1 = couple.get('name1', '')
            name2 = couple.get('name2', '')
            if name1 and name2:
                pair_key = optimizer._get_pair_key(name1, name2)
                optimizer.pair_history[pair_key] += 3  # 大きな偽装値で回避

        # モード判定
        mode = request.form.get('mode', 'auto')
        
        if mode == 'hybrid':
            # ハイブリッドモード: 手動日程を受け取り、残りを自動最適化
            manual_days_json = request.form.get('manual_days', '[]')
            manual_days = json.loads(manual_days_json)
            
            # fixed_days 形式に変換
            fixed_days = []
            for md in manual_days:
                fixed_days.append({
                    'day': md['day'],
                    'groups': md['groups']
                })
            
            schedule = optimizer.make_groups(num_groups, num_days, fixed_days=fixed_days)
            message = f"ハイブリッドモード: 手動{len(fixed_days)}日 + 自動{num_days - len(fixed_days)}日でグループ分けしました！"
        else:
            # 全自動モード（従来通り）
            schedule = optimizer.make_groups(num_groups, num_days)
            message = "条件を考慮してグループ分けしました！メンバーをドラッグ＆ドロップで手動調整できます。"

        # 手動保存のためのデータを準備
        schedule_json = json.dumps(schedule, ensure_ascii=False)

        # DBの履歴データをJavaScriptで扱いやすい形式に変換
        js_history = {f"{k[0]}::{k[1]}": v for k, v in existing_history.items()}
        db_history_json = json.dumps(js_history, ensure_ascii=False)

        # 恋人ペアデータも結果画面に渡す
        couples_json_for_result = json.dumps(couples, ensure_ascii=False)

        return render_template('result.html', schedule=schedule, message=message, schedule_json=schedule_json, db_history_json=db_history_json, couples_json=couples_json_for_result)

    return render_template('index.html')


def save_groups_to_db_fixed(schedule):
    for day in schedule:
        for group in day['groups']:
            # groupの中身が [{'name':..., 'grade':..., 'gender':...}, ...] となっている
            clean_names = [p['name'] for p in group]
            
            for p1, p2 in combinations(clean_names, 2):
                sorted_p1, sorted_p2 = sorted((p1, p2))
                record = PairHistory.query.filter_by(person1=sorted_p1, person2=sorted_p2).first()
                if record:
                    record.count += 1
                else:
                    db.session.add(new_record := PairHistory(person1=sorted_p1, person2=sorted_p2, count=1))
    db.session.commit()

# --- 履歴リセット機能（おまけ） ---
@app.route('/reset')
def reset_db():
    # データを全削除する機能（開発中に便利）
    db.session.query(PairHistory).delete()
    db.session.commit()
    return "履歴を全てリセットしました。<a href='/'>戻る</a>"

@app.route('/save_result', methods=['POST'])
def save_result():
    schedule_json = request.form.get('schedule_data')
    if schedule_json:
        try:
            schedule = json.loads(schedule_json)
            save_groups_to_db_fixed(schedule)
            return "<h1>データベースに保存しました。</h1><br><a href='/'>トップに戻る</a>"
        except Exception as e:
            return f"保存中にエラーが発生しました: {e}", 500
    return "データが見つかりません", 400
    return "履歴を全てリセットしました。<a href='/'>戻る</a>"

if __name__ == '__main__':
    app.run(debug=True)
    
@app.route('/api/history')
def api_history():
    """履歴データをJSON形式で返すAPI"""
    records = PairHistory.query.order_by(PairHistory.count.desc()).all()
    pairs = []
    for r in records:
        pairs.append({
            'person1': r.person1,
            'person2': r.person2,
            'count': r.count
        })
    
    total_pairs = len(pairs)
    total_count = sum(r.count for r in records)
    
    return {
        'pairs': pairs,
        'total_pairs': total_pairs,
        'total_count': total_count
    }

@app.route('/debug/history')
def debug_history():
    # 全データを取得
    records = PairHistory.query.all()
    
    # 簡易的なHTMLを作成（テンプレートファイルを作らなくて良いように）
    html = """
    <h1>📊 データベースの中身（デバッグ用）</h1>
    <a href="/">TOPに戻る</a>
    <table border="1" style="border-collapse: collapse; margin-top: 20px;">
        <tr style="background-color: #f2f2f2;">
            <th style="padding: 8px;">ID</th>
            <th style="padding: 8px;">人1</th>
            <th style="padding: 8px;">人2</th>
            <th style="padding: 8px;">一緒になった回数</th>
        </tr>
    """
    
    for r in records:
        html += f"""
        <tr>
            <td style="padding: 8px;">{r.id}</td>
            <td style="padding: 8px;">{r.person1}</td>
            <td style="padding: 8px;">{r.person2}</td>
            <td style="padding: 8px; text-align: center;">{r.count}</td>
        </tr>
        """
    
    html += "</table>"
    return html