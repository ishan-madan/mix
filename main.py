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
    
    def get_user_input(self) -> Tuple[int, List[str]]:
        """Get user input for max songs and style order"""
        while True:
            try:
                max_songs = int(input("Enter maximum number of distinct songs to use: "))
                if max_songs <= 0:
                    print("Please enter a positive number.")
                    continue
                break
            except ValueError:
                print("Please enter a valid number.")
        
        while True:
            styles_input = input("Enter the order of styles (comma-separated): ").strip()
            if not styles_input:
                print("Please enter at least one style.")
                continue
            
            styles = [style.strip().lower() for style in styles_input.split(',')]
            
            # Check if all styles exist in our database
            missing_styles = []
            for style in styles:
                if style not in self.songs_by_style:
                    missing_styles.append(style)
            
            if missing_styles:
                print(f"Warning: These styles are not found in the database: {missing_styles}")
                available_styles = list(self.songs_by_style.keys())
                print(f"Available styles: {', '.join(available_styles)}")
                continue_anyway = input("Continue anyway? (y/n): ").strip().lower()
                if continue_anyway != 'y':
                    continue
            
            break
        
        return max_songs, styles
    
    def find_all_mixes(self, max_songs: int, style_order: List[str]) -> List[List[Song]]:
        """Find all possible mixes using dynamic programming principles"""
        if not style_order:
            return []
        
        # Get songs for each required style
        songs_for_styles = []
        for style in style_order:
            style_songs = self.songs_by_style.get(style, [])
            if not style_songs:
                print(f"No songs found for style: {style}")
                return []
            songs_for_styles.append(style_songs)
        
        all_valid_mixes = []
        
        # Generate all possible combinations of songs up to max_songs
        for num_distinct_songs in range(1, min(max_songs, len(self.songs)) + 1):
            # Get all combinations of distinct songs
            for song_combination in itertools.combinations(self.songs, num_distinct_songs):
                song_set = set(song_combination)
                
                # Try to create a mix using only these songs
                valid_mixes = self._find_mixes_with_song_set(song_set, style_order)
                all_valid_mixes.extend(valid_mixes)
        
        return all_valid_mixes
    
    def _find_mixes_with_song_set(self, song_set: Set[Song], style_order: List[str]) -> List[List[Song]]:
        """Find all valid mixes using only songs from the given set"""
        # Use dynamic programming approach
        memo = {}
        
        def dp(position: int, last_song: Song = None) -> List[List[Song]]:
            """Recursive function with memoization"""
            if position == len(style_order):
                return [[]]  # Empty list means we've successfully filled all positions
            
            # Create a key for memoization
            key = (position, last_song.name if last_song else None)
            if key in memo:
                return memo[key]
            
            required_style = style_order[position]
            valid_mixes = []
            
            # Find songs in our set that have the required style
            candidates = [song for song in song_set if required_style in song.styles]
            
            for candidate in candidates:
                # Check if this song can mix with the last song
                if last_song is None or self.can_mix(last_song.camelot, candidate.camelot):
                    # Recursively find mixes for the remaining positions
                    remaining_mixes = dp(position + 1, candidate)
                    
                    # Add current candidate to each valid remaining mix
                    for remaining_mix in remaining_mixes:
                        valid_mixes.append([candidate] + remaining_mix)
            
            memo[key] = valid_mixes
            return valid_mixes
        
        return dp(0)
    
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
    generator = SongMixGenerator()
    
    # Load songs from CSV
    filename = input("Enter the CSV filename (or press Enter for 'songs.csv'): ").strip()
    if not filename:
        filename = "songs.csv"
    
    if not generator.load_songs_from_csv(filename):
        return
    
    if not generator.songs:
        print("No songs loaded. Please check your CSV file.")
        return
    
    print(f"\nAvailable styles: {', '.join(generator.songs_by_style.keys())}")
    
    # Get user input
    max_songs, style_order = generator.get_user_input()
    
    print(f"\nSearching for mixes with max {max_songs} distinct songs...")
    print(f"Style order: {' -> '.join(style_order)}")
    
    # Find all possible mixes
    mixes = generator.find_all_mixes(max_songs, style_order)
    
    # Display results
    generator.display_results(mixes, max_songs, style_order)

if __name__ == "__main__":
    main()