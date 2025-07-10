from flask import Flask, session, render_template, request, redirect, url_for, abort, send_from_directory
import os
import shutil
from functools import wraps

app = Flask(__name__)
app.secret_key = 'something-very-secret'
STATIC_DIR = 'static'  # this should be different than your main site

# ---------- 🔐 LOGIN PROTECTION ----------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('fae_logged_in'):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated

# ---------- 🔑 LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == 'moonstone':
            session['fae_logged_in'] = True
            return redirect(url_for('animal_index'))
        return render_template('fae_login.html', error="Incorrect password.")
    return render_template('fae_login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------- 🦄 MAIN GALLERY ----------
@app.route('/')
@login_required
def animal_index():
    animals = [name for name in sorted(os.listdir(STATIC_DIR)) if os.path.isdir(os.path.join(STATIC_DIR, name))]
    return render_template('animal_index.html', animals=animals)

@app.route('/<animal>')
@login_required
def animal_gallery(animal):
    base_path = os.path.join(STATIC_DIR, animal)
    if not os.path.isdir(base_path):
        abort(404)

    folders = []
    for folder_name in sorted(os.listdir(base_path)):
        folder_path = os.path.join(base_path, folder_name)
        if os.path.isdir(folder_path):
            for file_name in sorted(os.listdir(folder_path)):
                if file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    folders.append({
                        'name': f"{animal}/{folder_name}",
                        'thumbnail': f"{animal}/{folder_name}/{file_name}",
                        'label': folder_name
                    })
                    break

    return render_template('index.html', folders=folders, animal=animal)

@app.route('/board/<path:board_name>')
@login_required
def board(board_name):
    board_path = os.path.join(STATIC_DIR, board_name)
    if not os.path.exists(board_path):
        abort(404)

    images = [f for f in sorted(os.listdir(board_path)) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
    animal = board_name.split('/')[0] if '/' in board_name else None

    return render_template('board.html', board_name=board_name, images=images, animal=animal)

# ---------- 🌟 FAVORITES ----------
@app.route('/favorites')
@login_required
def show_favorites():
    fav_path = os.path.join(STATIC_DIR, 'favorites')
    if not os.path.isdir(fav_path):
        return render_template('index.html', folders=[], animal="favorites")

    folders = [{
        'name': 'favorites',
        'thumbnail': f"favorites/{img}",
        'label': img
    } for img in sorted(os.listdir(fav_path)) if img.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]

    return render_template('index.html', folders=folders, animal="favorites")

@app.route('/favorite', methods=['POST'])
@login_required
def favorite():
    rel_path = request.form.get('image_path')
    if not rel_path:
        abort(400)

    src_path = os.path.join(STATIC_DIR, rel_path)
    fav_dir = os.path.join(STATIC_DIR, 'favorites')
    os.makedirs(fav_dir, exist_ok=True)

    filename = os.path.basename(rel_path)
    dest_path = os.path.join(fav_dir, filename)

    if not os.path.exists(dest_path):
        shutil.copy2(src_path, dest_path)

    return redirect(request.headers.get("Referer", "/"))

# ---------- ❌ DELETE ----------
@app.route('/delete', methods=['POST'])
@login_required
def delete_image():
    rel_path = request.form.get('image_path')
    if not rel_path:
        abort(400)

    src_path = os.path.join(STATIC_DIR, rel_path)
    deleted_dir = os.path.join('deleted_fae', 'deleted')
    os.makedirs(deleted_dir, exist_ok=True)

    filename = os.path.basename(rel_path)
    dest_path = os.path.join(deleted_dir, filename)

    if os.path.exists(src_path):
        shutil.move(src_path, dest_path)
    else:
        print(f"[ERROR] File not found: {src_path}")

    return redirect(request.headers.get("Referer", "/"))

# ---------- 📁 STATIC FILES ----------
@app.route('/static/<path:filename>')
@login_required
def static_file(filename):
    return send_from_directory(STATIC_DIR, filename)

# ---------- 🧪 RUN ----------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)