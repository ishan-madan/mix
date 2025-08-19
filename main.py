import csv
from collections import defaultdict
from typing import List, Dict, Tuple, Set
import itertools

class Song:
    def __init__(self, name: str, artist: str, camelot: str, styles: List[str]):
        self.name = name
        self.artist = artist
        self.camelot = camelot
        self.styles = styles
    
    def __str__(self):
        return f"{self.name} by {self.artist} ({self.camelot}) - {', '.join(self.styles)}"

class SongMixGenerator:
    def __init__(self):
        self.songs = []
        self.songs_by_style = defaultdict(list)
    
    # loads all songs from the CSV file we have saved
    def load_songs_from_csv(self, filename: str):
        """Load songs from CSV file"""
        try:
            with open(filename, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    name = row['name'].strip()
                    artist = row['artist'].strip()
                    camelot = row['camelot'].strip().upper()
                    styles_str = row['style'].strip()
                    
                    # Parse styles (comma-separated)
                    styles = [style.strip().lower() for style in styles_str.split(',')]
                    
                    song = Song(name, artist, camelot, styles)
                    self.songs.append(song)
                    
                    # Index songs by style for efficient lookup
                    for style in styles:
                        self.songs_by_style[style].append(song)
                        
            print(f"Loaded {len(self.songs)} songs from {filename}")
            for song in self.songs:
                print(f"Song: {song}")
            
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
            return False
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return False
        
        return True
    
    # seperate the camelot into a number and a letter
    def parse_camelot(self, camelot: str) -> Tuple[int, str]:
        """Parse camelot string into number and letter"""
        if len(camelot) < 2:
            raise ValueError(f"Invalid camelot format: {camelot}")
        
        number_str = camelot[:-1]
        letter = camelot[-1].upper()
        
        try:
            number = int(number_str)
        except ValueError:
            raise ValueError(f"Invalid camelot number: {number_str}")
            
        if not (1 <= number <= 12):
            raise ValueError(f"Camelot number must be between 1 and 12: {number}")
            
        if letter not in ['A', 'B']:
            raise ValueError(f"Camelot letter must be A or B: {letter}")
            
        return number, letter
    
    # checks if 2 songs can mix together
    def can_mix(self, camelot1: str, camelot2: str) -> bool:
        """Check if two songs can be mixed based on Camelot rules"""
        try:
            num1, letter1 = self.parse_camelot(camelot1)
            num2, letter2 = self.parse_camelot(camelot2)
        except ValueError:
            return False
        
        # Rule 1: Same number, same letter
        if num1 == num2 and letter1 == letter2:
            return True
        
        # Rule 2: Same number, different letter
        if num1 == num2 and letter1 != letter2:
            return True
        
        # Rule 3: Adjacent number (considering circular nature), same letter
        if letter1 == letter2:
            # Handle circular nature (12 -> 1, 1 -> 12)
            diff = abs(num1 - num2)
            if diff == 1 or diff == 11:  # 11 means going from 1 to 12 or vice versa
                return True
        
        return False
    
    # generates a mep of the song combos that can be used for a mix
    def generate_mixes_map(self, max_songs: int, style_order: List[str]) -> Dict[frozenset, List[List[Song]]]:
        """Generate all valid mixes and store them in a hashmap by distinct song sets"""
        mixes_map = {}
        
        # Generate all combinations of distinct songs up to max_songs
        for num_distinct_songs in range(1, min(max_songs, len(self.songs)) + 1):
            for song_combination in itertools.combinations(self.songs, num_distinct_songs):
                song_set = set(song_combination)
                
                # Generate valid mixes for this set
                valid_mixes = self._find_mixes_with_song_set(song_set, style_order)
                
                if valid_mixes:
                    # Only store sets that have at least one valid mix
                    mixes_map[frozenset(song_set)] = valid_mixes
        
        return mixes_map

    # find all possible mixes with a given set of songs
    def _find_mixes_with_song_set(self, song_set: Set[Song], style_order: List[str]) -> List[List[Song]]:
        """Find all valid mixes using only songs from the given set,
        ensuring all songs in the set are used at least once"""
        
        # Original DP function
        memo = {}
        
        def dp(position: int, last_song: Song = None) -> List[List[Song]]:
            if position == len(style_order):
                return [[]]
            
            key = (position, last_song.name if last_song else None)
            if key in memo:
                return memo[key]
            
            required_style = style_order[position]
            valid_mixes = []
            candidates = [song for song in song_set if required_style in song.styles]
            
            for candidate in candidates:
                if last_song is None or self.can_mix(last_song.camelot, candidate.camelot):
                    remaining_mixes = dp(position + 1, candidate)
                    for remaining_mix in remaining_mixes:
                        valid_mixes.append([candidate] + remaining_mix)
            
            memo[key] = valid_mixes
            return valid_mixes
        
        # Generate all mixes
        all_mixes = dp(0)
        
        # Filter to ensure all songs in the set are used at least once
        filtered_mixes = []
        for mix in all_mixes:
            mix_set = set(mix)
            if mix_set == song_set:
                filtered_mixes.append(mix)
        
        return filtered_mixes
    
    # displays all mixes
    def display_results(self, mixes: List[List[Song]], max_songs: int, style_order: List[str]):
        """Display the results"""
        if not mixes:
            print(f"\nNo valid mixes found for styles: {', '.join(style_order)} with max {max_songs} distinct songs.")
            return
        
        print(f"\nFound {len(mixes)} valid mix(es) for styles: {', '.join(style_order)}")
        print(f"Maximum distinct songs allowed: {max_songs}")
        print("-" * 80)
        
        for i, mix in enumerate(mixes, 1):
            print(f"\nMix #{i}:")
            distinct_songs = set(song.name for song in mix)
            print(f"Uses {len(distinct_songs)} distinct songs: {', '.join(distinct_songs)}")
            
            for j, song in enumerate(mix):
                style_needed = style_order[j]
                print(f"  {j+1}. [{style_needed.upper()}] {song}")
                
                # Show mixing compatibility
                if j > 0:
                    prev_song = mix[j-1]
                    compatible = self.can_mix(prev_song.camelot, song.camelot)
                    print(f"      Camelot transition: {prev_song.camelot} -> {song.camelot} ({'✓' if compatible else '✗'})")
            
            print("-" * 40)

def main():
    # === Configuration (set in code) ===
    csv_file_path = "songs.csv"                # CSV file path
    max_songs = 3                              # Maximum number of distinct songs to use
    style_order = ["hikk", "fast", "drop", "fast", "slow", "drop"]    # Order of styles

    generator = SongMixGenerator()

    # Load songs from CSV
    if not generator.load_songs_from_csv(csv_file_path):
        return
    if not generator.songs:
        print("No songs loaded. Please check your CSV file.")
        return

    print(f"\nAvailable styles: {', '.join(generator.songs_by_style.keys())}")
    print(f"Using max_songs = {max_songs}")
    print(f"Style order = {' -> '.join(style_order)}")

    # === Step 1: generate hashmap of valid mixes ===
    print("\nGenerating all valid mixes...")
    mixes_map = generator.generate_mixes_map(max_songs, style_order)

    if not mixes_map:
        print("No valid mixes found for the given styles.")
        return

    # === Step 2: display distinct sets (keys of the hashmap) ===
    song_sets_list = list(mixes_map.keys())
    print(f"\nFound {len(song_sets_list)} distinct song set(s) with at least one valid mix:")
    for i, s in enumerate(song_sets_list, 1):
        names = [song.name for song in s]
        print(f"{i}. {', '.join(names)}")

    # === Step 3: ask user which set to display ===
    while True:
        try:
            choice = int(input("\nEnter the set number you are interested in: "))
            if 1 <= choice <= len(song_sets_list):
                chosen_set_key = song_sets_list[choice - 1]
                break
            else:
                print("Invalid choice. Try again.")
        except ValueError:
            print("Please enter a valid number.")

    # === Step 4: display all mixes for the chosen set ===
    chosen_mixes = mixes_map[chosen_set_key]
    print(f"\nGenerating mixes for chosen set #{choice}...")
    generator.display_results(chosen_mixes, len(chosen_set_key), style_order)




if __name__ == "__main__":
    main()