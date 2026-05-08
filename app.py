import os
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify
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

# メンバー名簿マスター: 名前・学年・性別・工具係を保存
class MemberMaster(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    grade = db.Column(db.String(10), nullable=False, default='1')
    gender = db.Column(db.String(10), nullable=False, default='M')
    is_tool = db.Column(db.Boolean, default=False)

# 企画（イベント）: 企画名と参加メンバーを保存
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(20), default='')  # YYYY-MM-DD など自由形式
    participants_json = db.Column(db.Text, default='[]')  # JSON: [{name, grade, gender, is_tool}, ...]
    num_days = db.Column(db.Integer, default=3)
    num_groups = db.Column(db.Integer, default=4)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

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

        # 手動日程（確定済み）を受け取り、残りを自動最適化
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
        message = f"グループ分けしました！"
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

# --- メンバー名簿API ---
@app.route('/api/members', methods=['GET'])
def api_members_list():
    """名簿の全メンバーをJSON形式で返す"""
    members = MemberMaster.query.order_by(MemberMaster.name).all()
    return jsonify([{
        'id': m.id,
        'name': m.name,
        'grade': m.grade,
        'gender': m.gender,
        'is_tool': m.is_tool
    } for m in members])

@app.route('/api/members/search', methods=['GET'])
def api_members_search():
    """名前で部分一致検索"""
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    members = MemberMaster.query.filter(MemberMaster.name.contains(q)).order_by(MemberMaster.name).limit(20).all()
    return jsonify([{
        'id': m.id,
        'name': m.name,
        'grade': m.grade,
        'gender': m.gender,
        'is_tool': m.is_tool
    } for m in members])

@app.route('/api/members', methods=['POST'])
def api_members_add():
    """メンバーを名簿に追加（既に存在する場合は更新）"""
    data = request.get_json()
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': '名前が必要です'}), 400
    
    existing = MemberMaster.query.filter_by(name=name).first()
    if existing:
        existing.grade = data.get('grade', existing.grade)
        existing.gender = data.get('gender', existing.gender)
        existing.is_tool = data.get('is_tool', existing.is_tool)
    else:
        new_member = MemberMaster(
            name=name,
            grade=data.get('grade', '1'),
            gender=data.get('gender', 'M'),
            is_tool=data.get('is_tool', False)
        )
        db.session.add(new_member)
    db.session.commit()
    member = existing if existing else new_member
    return jsonify({'status': 'ok', 'id': member.id})

@app.route('/api/members/bulk', methods=['POST'])
def api_members_bulk_add():
    """複数メンバーを一括登録（参加者一覧から名簿に保存）"""
    data = request.get_json()
    members_data = data.get('members', [])
    added = 0
    updated = 0
    for m in members_data:
        name = m.get('name', '').strip()
        if not name:
            continue
        existing = MemberMaster.query.filter_by(name=name).first()
        if existing:
            existing.grade = m.get('grade', existing.grade)
            existing.gender = m.get('gender', existing.gender)
            existing.is_tool = m.get('is_tool', existing.is_tool)
            updated += 1
        else:
            new_member = MemberMaster(
                name=name,
                grade=m.get('grade', '1'),
                gender=m.get('gender', 'M'),
                is_tool=m.get('is_tool', False)
            )
            db.session.add(new_member)
            added += 1
    db.session.commit()
    return jsonify({'status': 'ok', 'added': added, 'updated': updated})

@app.route('/api/members/<int:member_id>', methods=['DELETE'])
def api_members_delete(member_id):
    """メンバーを名簿から削除"""
    member = MemberMaster.query.get(member_id)
    if member:
        db.session.delete(member)
        db.session.commit()
        return jsonify({'status': 'ok'})
    return jsonify({'error': '見つかりません'}), 404

@app.route('/api/members/reset', methods=['POST'])
def api_members_reset():
    """名簿を全削除"""
    db.session.query(MemberMaster).delete()
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/members/<int:member_id>', methods=['PUT'])
def api_members_update(member_id):
    """メンバー情報を更新"""
    member = MemberMaster.query.get(member_id)
    if not member:
        return jsonify({'error': '見つかりません'}), 404
    data = request.get_json()
    if 'name' in data:
        new_name = data['name'].strip()
        if new_name:
            member.name = new_name
    if 'grade' in data:
        member.grade = data['grade']
    if 'gender' in data:
        member.gender = data['gender']
    if 'is_tool' in data:
        member.is_tool = data['is_tool']
    db.session.commit()
    return jsonify({'status': 'ok', 'member': {
        'id': member.id,
        'name': member.name,
        'grade': member.grade,
        'gender': member.gender,
        'is_tool': member.is_tool
    }})

@app.route('/api/members/promote', methods=['POST'])
def api_members_promote():
    """学年を一括進級（1→2→3→4→M1→M2→卒業）"""
    data = request.get_json() or {}
    delete_graduated = data.get('delete_graduated', False)

    promotion_map = {'1': '2', '2': '3', '3': '4', '4': 'M1', 'M1': 'M2'}
    members = MemberMaster.query.all()
    promoted = 0
    graduated = 0
    graduated_names = []

    for m in members:
        if m.grade == 'M2':
            graduated += 1
            graduated_names.append(m.name)
            if delete_graduated:
                db.session.delete(m)
        elif m.grade in promotion_map:
            m.grade = promotion_map[m.grade]
            promoted += 1

    db.session.commit()
    return jsonify({
        'status': 'ok',
        'promoted': promoted,
        'graduated': graduated,
        'graduated_names': graduated_names
    })

# ===== 企画管理 API =====
@app.route('/api/events', methods=['GET'])
def api_events_list():
    """企画一覧を取得"""
    events = Event.query.order_by(Event.updated_at.desc()).all()
    return jsonify([{
        'id': e.id, 'name': e.name, 'date': e.date,
        'participant_count': len(json.loads(e.participants_json or '[]')),
        'num_days': e.num_days, 'num_groups': e.num_groups,
        'created_at': str(e.created_at) if e.created_at else '',
        'updated_at': str(e.updated_at) if e.updated_at else ''
    } for e in events])

@app.route('/api/events', methods=['POST'])
def api_events_create():
    """企画を新規作成"""
    data = request.get_json()
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': '企画名が必要です'}), 400
    event = Event(
        name=name,
        date=data.get('date', ''),
        participants_json=json.dumps(data.get('participants', []), ensure_ascii=False),
        num_days=data.get('num_days', 3),
        num_groups=data.get('num_groups', 4)
    )
    db.session.add(event)
    db.session.commit()
    return jsonify({'status': 'ok', 'id': event.id})

@app.route('/api/events/<int:event_id>', methods=['GET'])
def api_events_get(event_id):
    """企画の詳細（参加者リスト含む）を取得"""
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({'error': '見つかりません'}), 404
    return jsonify({
        'id': event.id, 'name': event.name, 'date': event.date,
        'participants': json.loads(event.participants_json or '[]'),
        'num_days': event.num_days, 'num_groups': event.num_groups
    })

@app.route('/api/events/<int:event_id>', methods=['PUT'])
def api_events_update(event_id):
    """企画を更新（参加者リスト・設定を保存）"""
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({'error': '見つかりません'}), 404
    data = request.get_json()
    if 'name' in data:
        event.name = data['name'].strip()
    if 'date' in data:
        event.date = data['date']
    if 'participants' in data:
        event.participants_json = json.dumps(data['participants'], ensure_ascii=False)
    if 'num_days' in data:
        event.num_days = data['num_days']
    if 'num_groups' in data:
        event.num_groups = data['num_groups']
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
def api_events_delete(event_id):
    """企画を削除"""
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({'error': '見つかりません'}), 404
    db.session.delete(event)
    db.session.commit()
    return jsonify({'status': 'ok'})

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