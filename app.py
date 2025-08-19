from flask import Flask, request, render_template, redirect, url_for
import csv
from io import StringIO
from collections import defaultdict
from song_mix_generator import Song, SongMixGenerator

app = Flask(__name__)
generator = SongMixGenerator()
uploaded_csv = None
mixes_map = {}

@app.route("/", methods=["GET", "POST"])
def index():
    global uploaded_csv
    if request.method == "POST":
        file = request.files.get("csv_file")
        if file:
            uploaded_csv = StringIO(file.stream.read().decode("utf-8"))
            uploaded_csv.seek(0)
            # Load songs
            generator.songs = []
            generator.songs_by_style = defaultdict(list)
            reader = csv.DictReader(uploaded_csv)
            for row in reader:
                name = row['name'].strip()
                artist = row['artist'].strip()
                camelot = row['camelot'].strip().upper()
                styles = [s.strip().lower() for s in row['style'].split(',')]
                song = Song(name, artist, camelot, styles)
                generator.songs.append(song)
                for style in styles:
                    generator.songs_by_style[style].append(song)
            styles_list = sorted(generator.songs_by_style.keys())
            return render_template("order.html", styles=styles_list)
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    global mixes_map
    data = request.get_json()
    style_order = data.get("styleOrder", [])
    max_songs = int(data.get("maxSongs", 3))
    
    # Generate all valid mixes grouped by song set
    mixes_map = generator.generate_mixes_map(max_songs, style_order)
    
    if not mixes_map:
        return "<h3>No valid mixes found for the given styles.</h3>"
    
    song_sets_list = list(mixes_map.keys())
    sets_info = [{"index": i+1, "names": [song.name for song in s]} for i, s in enumerate(song_sets_list)]
    
    return render_template("sets.html", sets=sets_info)

@app.route("/view_set/<int:set_index>")
def view_set(set_index):
    song_sets_list = list(mixes_map.keys())
    if 1 <= set_index <= len(song_sets_list):
        chosen_set_key = song_sets_list[set_index-1]
        chosen_mixes = mixes_map[chosen_set_key]
        # Pass generator to template for Camelot checks
        return render_template("mixes.html", mixes=chosen_mixes, generator=generator, enumerate=enumerate)
    else:
        return "<h3>Invalid set index.</h3>"

if __name__ == "__main__":
    app.run(debug=True)
