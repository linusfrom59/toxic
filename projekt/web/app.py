from flask import Flask, render_template, request
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ..database.db import init_db, save_submission, get_connection
app = Flask(
    __name__,
    template_folder=str(project_root / 'web' / 'templates'),
    static_folder=str(project_root / 'web' / 'static'),
)
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024

init_db()


@app.route('/')
def form():
    return render_template('form.html')


@app.route('/submit', methods=['POST'])
def submit():
    ingame_name = request.form.get('ingame_name', '').strip()
    age_group = request.form.get('age_group', '').strip()
    country = request.form.get('country', '').strip()
    highest_rank = request.form.get('highest_rank', '').strip()
    highest_trophies = request.form.get('highest_trophies', '').strip()
    club_member = request.form.get('club_member', '').strip()
    privacy_opened = request.form.get('privacy_opened', 'false')
    privacy_scrolled = request.form.get('privacy_scrolled', 'false')
    profile_image = request.files.get('profile_image')

    profile_image_name = ''
    if profile_image and profile_image.filename:
        uploads_dir = project_root / 'web' / 'static' / 'uploads'
        uploads_dir.mkdir(parents=True, exist_ok=True)
        safe_name = ''.join(ch for ch in profile_image.filename if ch.isalnum() or ch in '._-')
        profile_image_name = f"{ingame_name.replace(' ', '_')}_{safe_name}" if safe_name else ''
        if profile_image_name:
            profile_image.save(uploads_dir / profile_image_name)

    link_code = save_submission(
        ingame_name=ingame_name,
        age_group=age_group,
        country=country,
        highest_rank=highest_rank,
        highest_trophies=highest_trophies,
        club_member=club_member,
        profile_image=profile_image_name,
        privacy_opened=privacy_opened,
        privacy_scrolled=privacy_scrolled,
    )

    return render_template('success.html', link_code=link_code)


@app.route('/admin')
def admin():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submissions ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return render_template('admin.html', rows=rows)


if __name__ == '__main__':
    app.run(debug=True)
