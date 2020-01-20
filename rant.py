# 
#   Rant
#   Copyright (c) 2020 Yusuf Olokoba.
#

from argparse import ArgumentParser
from google.cloud.texttospeech import TextToSpeechClient, enums, types
from path import Path
from pdfminer.high_level import extract_text

# Parse args
parser = ArgumentParser(description="Rant")
parser.add_argument("-i", "--input", type=str, required=True, help="Path to input PDF file")
parser.add_argument("-o", "--output", type=str, required=True, help="Path to output directory")
parser.add_argument("-s", "--speed", type=float, default=1.7, help="Speech speed")
parser.add_argument("-r", "--remove", type=str, help="Remove text after this string. Use for stripping references.")
args = parser.parse_args()

# Create output dir
output_path = Path(args.output)
output_path.mkdir_p()

# Extract text
text = extract_text(args.input)

# Remove useless text
remove_index = text.find(args.remove)
if remove_index >= 0:
    text = text[:remove_index]

# Tokenize
words = text.split()
print(f"Extracted {len(words)} words from PDF")

# Chunk into sections so we don't exceed limit
chunks = []
current_chunk = []
current_chunk_count = 0
while words:
    word = words.pop(0)
    # Check if we've reached limit
    if current_chunk_count + len(word) >= 5000:
        chunk = " ".join(current_chunk)
        chunks.append(chunk)
        current_chunk = []
        current_chunk_count = 0
    # Add word to current chunk
    current_chunk.append(word)
    current_chunk_count += len(word) + 1 # Plus one for space character

print(f"Generated {len(chunks)} chunks for TTS conversion")

# Build TTS request
tts_client = TextToSpeechClient()
voice = types.VoiceSelectionParams(language_code="en-US", ssml_gender=enums.SsmlVoiceGender.NEUTRAL)
audio_config = types.AudioConfig(audio_encoding=enums.AudioEncoding.MP3, speaking_rate=args.speed)

# Convert text to speech
for i, chunk in enumerate(chunks):
    input = types.SynthesisInput(text=chunk)
    response = tts_client.synthesize_speech(input, voice, audio_config)
    with open(f"{output_path}/{i+1}.mp3", "wb") as output_file:
        output_file.write(response.audio_content)
        print(f"Wrote chunk {i+1}/{len(chunks)}")