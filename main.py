import json
import os
from moviepy import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    vfx,
    ColorClip
)
from moviepy.video.io.VideoFileClip import VideoFileClip
import numpy as np

def find_audio_file(base_path):
    """Try to find an audio file with different extensions"""
    base, ext = os.path.splitext(base_path)
    possible_extensions = ['.wav', '.mp3', '.ogg', '.m4a', '.aac']
    
    # Try the original extension first
    if os.path.exists(base_path):
        return base_path
    
    # Try other extensions
    for ext in possible_extensions:
        test_path = base + ext
        if os.path.exists(test_path):
            print(f"Found audio file: {test_path}")
            return test_path
    
    return None

def load_asset(path, asset_type="video"):
    """Load asset with error handling and path checking."""
    if asset_type == "audio":
        path = find_audio_file(path)
        if not path:
            print(f"Warning: No audio file found for '{path}' (tried .wav, .mp3, .ogg, .m4a, .aac)")
            return None
    elif not os.path.exists(path):
        print(f"Warning: {asset_type} file not found at '{path}'")
        return None
    
    try:
        if asset_type == "video" or asset_type == "gif":
            return VideoFileClip(path)
        elif asset_type == "audio":
            return AudioFileClip(path)
        elif asset_type == "image":
            return ImageClip(path)
    except Exception as e:
        print(f"Error loading {asset_type} file '{path}': {str(e)}")
        return None

def safe_subclip(clip, start_time, end_time):
    """Create a subclip with duration validation"""
    if end_time > clip.duration:
        print(f"Warning: Requested end_time ({end_time:.2f}s) exceeds clip duration ({clip.duration:.2f}s). Clipping to max duration.")
        end_time = clip.duration
    
    if start_time >= clip.duration:
        print(f"Warning: start_time ({start_time:.2f}s) exceeds clip duration ({clip.duration:.2f}s). Skipping this clip.")
        return None
    
    if start_time >= end_time:
        print(f"Warning: start_time ({start_time:.2f}s) must be less than end_time ({end_time:.2f}s). Skipping this clip.")
        return None
    
    return clip.subclipped(start_time, end_time)

def loop_clip(clip, duration):
    """Create a looped version of a clip to match the specified duration"""
    if clip.duration >= duration:
        return clip.subclipped(0, duration)
    
    # Calculate how many times we need to loop
    loops = int(duration / clip.duration) + 1
    
    # Create a list of looped clips
    looped_clips = [clip] * loops
    
    # Concatenate them
    concatenated = concatenate_videoclips(looped_clips)
    
    # Trim to exact duration
    return concatenated.subclipped(0, duration)

def find_font_file(font_name):
    """Try to find a font file on the system"""
    # Common font locations on Windows
    possible_paths = [
        font_name,  # Just the filename
        f"C:/Windows/Fonts/{font_name}",
        f"C:/Windows/Fonts/{font_name}.ttf",
        f"C:/Windows/Fonts/{font_name}.ttc",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), font_name),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{font_name}.ttf"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # If not found, try to use a default font
    default_fonts = ["arial.ttf", "times.ttf", "cour.ttf", "verdana.ttf"]
    for font in default_fonts:
        path = f"C:/Windows/Fonts/{font}"
        if os.path.exists(path):
            return path
    
    # If all else fails, return None and let TextClip use its default
    return None

def color_string_to_rgb(color_string):
    """Convert color string to RGB tuple"""
    color_map = {
        'white': (255, 255, 255),
        'black': (0, 0, 0),
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
        'yellow': (255, 255, 0),
        'cyan': (0, 255, 255),
        'magenta': (255, 0, 255),
        'orange': (255, 165, 0),
        'purple': (128, 0, 128),
        'pink': (255, 192, 203),
        'brown': (165, 42, 42),
        'gray': (128, 128, 128),
        'grey': (128, 128, 128),
        'gold': (255, 215, 0),
        'silver': (192, 192, 192)
    }
    
    # Convert to lowercase for case-insensitive matching
    color_lower = color_string.lower()
    
    if color_lower in color_map:
        return color_map[color_lower]
    else:
        # Try to parse as hex
        if color_string.startswith('#'):
            hex_color = color_string[1:]
            if len(hex_color) == 6:
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Default to white if color not recognized
        print(f"Warning: Color '{color_string}' not recognized, using white")
        return (255, 255, 255)

# Load JSON
with open("edit_config_advanced.json", "r") as f:
    config = json.load(f)

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Load assets with error handling
video_assets = {}
for v in config["assets"]["videos"]:
    path = os.path.join(script_dir, v["path"])
    clip = load_asset(path, "video")
    if clip:
        video_assets[v["name"]] = clip
        print(f"Loaded video '{v['name']}': duration {clip.duration:.2f}s")

gif_assets = {}
for g in config["assets"]["gifs"]:
    path = os.path.join(script_dir, g["path"])
    clip = load_asset(path, "gif")
    if clip:
        gif_assets[g["name"]] = clip
        print(f"Loaded GIF '{g['name']}': duration {clip.duration:.2f}s")

image_assets = {}
for i in config["assets"]["images"]:
    path = os.path.join(script_dir, i["path"])
    clip = load_asset(path, "image")
    if clip:
        image_assets[i["name"]] = clip

audio_assets = {}
for a in config["assets"]["audios"]:
    path = os.path.join(script_dir, a["path"])
    clip = load_asset(path, "audio")
    if clip:
        audio_assets[a["name"]] = clip
        print(f"Loaded audio '{a['name']}': duration {clip.duration:.2f}s")

print(f"\nLoaded assets summary:")
print(f"- Videos: {len(video_assets)}")
print(f"- GIFs: {len(gif_assets)}")
print(f"- Images: {len(image_assets)}")
print(f"- Audio: {len(audio_assets)}")

# Helper functions
def parse_position(position, video_size):
    """Convert position from ratio/keyword to absolute coordinates."""
    if isinstance(position, str):
        if position == "center":
            return ("center", "center")
        elif position == "top-center":
            return ("center", 0.1)
        elif position == "bottom-center":
            return ("center", 0.9)
        elif position == "top-left":
            return (0.1, 0.1)
        elif position == "top-right":
            return (0.9, 0.1)
        elif position == "bottom-left":
            return (0.1, 0.9)
        elif position == "bottom-right":
            return (0.9, 0.9)
    elif isinstance(position, list) and len(position) == 2:
        return (position[0] * video_size[0], position[1] * video_size[1])
    return ("center", "center")

def apply_effects(clip, effects):
    """Apply effects to a clip."""
    for effect in effects:
        if effect["type"] == "fadein":
            clip = clip.with_effects([vfx.FadeIn(effect["duration"])])
        elif effect["type"] == "fadeout":
            clip = clip.with_effects([vfx.FadeOut(effect["duration"])])
        elif effect["type"] == "glow":
            # Create a simple glow effect using blur and color overlay
            glow_color = color_string_to_rgb(effect["color"])
            radius = effect.get("radius", 5)
            
            # Create a blurred version of the clip
            try:
                # Use blur effect if available
                blurred_clip = clip.with_effects([vfx.GaussianBlur(radius)])
            except:
                # Fallback: just use the original clip
                blurred_clip = clip
            
            # Create a colored overlay
            color_layer = ColorClip(clip.size, color=glow_color, duration=clip.duration)
            color_layer = color_layer.with_opacity(0.3)  # Adjust opacity for glow intensity
            
            # Composite the original clip, blurred version, and color overlay
            glow_clip = CompositeVideoClip([blurred_clip, color_layer, clip])
            clip = glow_clip
            
        elif effect["type"] == "outline":
            # Simple outline effect using multiple copies of the text
            if hasattr(clip, 'txt'):  # Check if it's a text clip
                outline_color = color_string_to_rgb(effect["color"])
                outline_width = effect.get("width", 2)
                
                # Create outline by offsetting the text in 4 directions
                outlines = []
                for dx, dy in [(-outline_width, 0), (outline_width, 0), (0, -outline_width), (0, outline_width)]:
                    outline = TextClip(
                        text=clip.txt,
                        font=clip.font,
                        font_size=clip.fontsize,
                        color=outline_color
                    ).with_duration(clip.duration).with_position((dx, dy))
                    outlines.append(outline)
                
                # Composite outlines and original text
                clip = CompositeVideoClip(outlines + [clip])
                
        elif effect["type"] == "shadow":
            # Simple shadow effect
            if hasattr(clip, 'txt'):  # Check if it's a text clip
                shadow_color = color_string_to_rgb(effect.get("color", "black"))
                shadow_offset = effect.get("offset", [5, 5])
                shadow_opacity = effect.get("opacity", 0.5)
                
                # Create shadow
                shadow = TextClip(
                    text=clip.txt,
                    font=clip.font,
                    font_size=clip.fontsize,
                    color=shadow_color
                ).with_duration(clip.duration)
                
                # Position shadow with offset
                shadow = shadow.with_position((
                    clip.pos[0] + shadow_offset[0] if isinstance(clip.pos[0], (int, float)) else clip.pos[0],
                    clip.pos[1] + shadow_offset[1] if isinstance(clip.pos[1], (int, float)) else clip.pos[1]
                ))
                
                shadow = shadow.with_opacity(shadow_opacity)
                
                # Composite shadow and original text
                clip = CompositeVideoClip([shadow, clip])
    
    return clip

def create_typewriter_effect(clip, duration):
    """Create a typewriter effect using multiple text clips"""
    if not hasattr(clip, 'txt'):
        # If not a text clip, just return with fade effect
        return clip.with_effects([vfx.FadeIn(duration)])
    
    text = clip.txt
    if not text:
        return clip
    
    # Split text into characters for character-by-character reveal
    characters = list(text)
    char_duration = duration / len(characters)
    
    # Create individual clips for each character
    char_clips = []
    
    for i, char in enumerate(characters):
        # Create a text clip for just this character
        char_clip = TextClip(
            text=char,
            font=clip.font,
            font_size=clip.fontsize,
            color=clip.color
        ).with_duration(char_duration)
        
        # Position this character relative to the start
        # This is a simplified version - in practice, you'd need to calculate proper positioning
        char_clip = char_clip.with_position(clip.pos)
        
        # Set the start time for this character
        char_clip = char_clip.with_start(i * char_duration)
        
        char_clips.append(char_clip)
    
    # Composite all character clips
    if char_clips:
        return CompositeVideoClip(char_clips)
    else:
        return clip

def apply_animation(clip, animation, video_size):
    """Apply animation to a clip."""
    if animation["type"] == "bounce":
        # FIXED: Parse the position and store it as a tuple before applying animation
        position = parse_position(clip.pos, video_size)
        
        def bounce_pos(t):
            # Get the original y position
            if isinstance(position[1], (int, float)):
                y_pos = position[1]
            else:
                y_pos = video_size[1] * 0.5  # Default to center if not a number
            
            # Calculate bounce offset
            bounce_height = animation.get("height", 20)
            offset = int(bounce_height * np.abs(np.sin(t * np.pi / animation["duration"])))
            
            # Return the new position
            return (position[0], y_pos - offset)
        
        clip = clip.with_position(bounce_pos)
        
    elif animation["type"] == "scroll":
        # FIXED: Parse the position and store it as a tuple before applying animation
        position = parse_position(clip.pos, video_size)
        
        # Get the original y position
        if isinstance(position[1], (int, float)):
            original_y = position[1]
        else:
            original_y = video_size[1] * 0.5  # Default to center if not a number
            
        if animation["direction"] == "left_to_right":
            clip = clip.with_position(lambda t: (-clip.w + t * clip.w / animation["duration"], original_y))
        elif animation["direction"] == "right_to_left":
            clip = clip.with_position(lambda t: (video_size[0] + clip.w - t * clip.w / animation["duration"], original_y))
            
    elif animation["type"] == "typewriter":
        # Use a simpler approach that doesn't require BitmapClip
        try:
            # Try the character-by-character approach
            clip = create_typewriter_effect(clip, animation["duration"])
        except Exception as e:
            print(f"Character-by-character typewriter failed: {str(e)}")
            # Fallback to simple fade-in effect
            clip = clip.with_effects([vfx.FadeIn(animation["duration"])])
    
    return clip

# Calculate total video duration to fix timing issues
total_duration = 0
for edit in config["editing"]:
    asset_name = edit["asset"]
    if asset_name in video_assets:
        original_duration = video_assets[asset_name].duration
        requested_duration = edit["end_time"] - edit["start_time"]
        actual_duration = min(requested_duration, original_duration - edit["start_time"])
        if actual_duration > 0:
            total_duration += actual_duration

print(f"\nCalculated total video duration: {total_duration:.2f}s")

# Process main editing
main_clips = []
current_time = 0

for edit in config["editing"]:
    # Check if 'asset' key exists
    if "asset" not in edit:
        print(f"Warning: Missing 'asset' key in edit entry: {edit}")
        continue
        
    asset_name = edit["asset"]
    if asset_name in video_assets:
        original_clip = video_assets[asset_name]
        
        # Fix timing - use current_time instead of edit["start_time"]
        start_time = min(edit["start_time"], original_clip.duration - 0.1)  # -0.1 to ensure at least 0.1s duration
        end_time = min(edit["end_time"], original_clip.duration)
        
        print(f"\nProcessing edit: {asset_name} from {start_time}s to {end_time}s")
        print(f"Original clip duration: {original_clip.duration:.2f}s")
        
        clip = safe_subclip(original_clip, start_time, end_time)
        if clip is None:
            print(f"Skipping edit for {asset_name} due to invalid time range")
            continue
            
        print(f"Created subclip: {clip.duration:.2f}s")
        clip = apply_effects(clip, edit.get("effects", []))
        main_clips.append(clip)
        current_time += clip.duration
    else:
        print(f"Warning: Video asset '{asset_name}' not found, skipping edit")

# Create final video
if main_clips:
    final_video = concatenate_videoclips(main_clips)
    print(f"\nFinal video duration: {final_video.duration:.2f}s")
else:
    print("\nNo valid video clips found, creating black background")
    final_video = ColorClip((1920, 1080), color=(0, 0, 0), duration=30)

# Process overlays
overlay_clips = []
for overlay in config["overlays"]:
    print(f"\nProcessing overlay: {overlay['type']} - {overlay.get('asset', overlay.get('text', 'N/A'))}")
    
    # Create the base clip based on type
    clip = None
    
    if overlay["type"] == "video":
        # Check if 'asset' key exists
        if "asset" not in overlay:
            print(f"Warning: Missing 'asset' key in video overlay: {overlay}")
            continue
            
        asset_name = overlay["asset"]
        if asset_name in video_assets:
            original_clip = video_assets[asset_name]
            clip = safe_subclip(original_clip, overlay["start_time"], overlay["end_time"])
            if clip is None:
                print(f"Skipping video overlay due to invalid time range")
                continue
        else:
            print(f"Warning: Video asset '{asset_name}' not found for overlay")
            continue
            
    elif overlay["type"] == "gif":
        # Check if 'asset' key exists
        if "asset" not in overlay:
            print(f"Warning: Missing 'asset' key in GIF overlay: {overlay}")
            continue
            
        asset_name = overlay["asset"]
        if asset_name in gif_assets:
            original_clip = gif_assets[asset_name]
            duration = overlay["end_time"] - overlay["start_time"]
            if duration > original_clip.duration:
                print(f"Looping GIF from {original_clip.duration:.2f}s to {duration:.2f}s")
                clip = loop_clip(original_clip, duration)
            else:
                clip = safe_subclip(original_clip, 0, duration)
        else:
            print(f"Warning: GIF asset '{asset_name}' not found for overlay")
            continue
            
    elif overlay["type"] == "image":
        # Check if 'asset' key exists
        if "asset" not in overlay:
            print(f"Warning: Missing 'asset' key in image overlay: {overlay}")
            continue
            
        asset_name = overlay["asset"]
        if asset_name in image_assets:
            duration = overlay["end_time"] - overlay["start_time"]
            clip = image_assets[asset_name].with_duration(duration)
        else:
            print(f"Warning: Image asset '{asset_name}' not found for overlay")
            continue
            
    elif overlay["type"] == "text":
        duration = overlay["end_time"] - overlay["start_time"]
        try:
            # Try to find the font file
            font_path = find_font_file(overlay.get("font", "Arial.ttf"))
            if font_path:
                print(f"Using font: {font_path}")
            else:
                print("Font not found, using default")
                font_path = None
                
            # Convert color string to RGB tuple
            color_rgb = color_string_to_rgb(overlay["color"])
            
            clip = TextClip(
                text=overlay["text"],
                font=font_path,
                font_size=overlay["font_size"],
                color=color_rgb  # Use RGB tuple instead of string
            ).with_duration(duration)
            
            # Add background if specified
            if "background" in overlay:
                bg_color = color_string_to_rgb(overlay["background"]["color"])
                bg = ColorClip(
                    clip.size,
                    color=bg_color,
                    duration=clip.duration
                ).with_opacity(overlay["background"]["opacity"])
                clip = CompositeVideoClip([bg, clip])
        except Exception as e:
            print(f"Error creating text clip: {str(e)}")
            continue
    
    if clip is None:
        print(f"Warning: Could not create {overlay['type']} overlay")
        continue
    
    # Apply size
    if "size" in overlay:
        clip = clip.resized((overlay["size"][0] * final_video.w, overlay["size"][1] * final_video.h))

    # Apply position
    position = parse_position(overlay["position"], final_video.size)
    clip = clip.with_position(position)

    # Apply opacity
    if "opacity" in overlay:
        clip = clip.with_opacity(overlay["opacity"])

    # Apply effects
    if "effects" in overlay:
        clip = apply_effects(clip, overlay["effects"])

    # Apply animation - FIXED: Pass video_size parameter
    if "animation" in overlay:
        clip = apply_animation(clip, overlay["animation"], final_video.size)

    # Set start time
    clip = clip.with_start(overlay["start_time"])
    overlay_clips.append(clip)
    print(f"Added overlay: duration {clip.duration:.2f}s, start at {overlay['start_time']}s")

# Composite all overlays
if overlay_clips:
    final_video = CompositeVideoClip([final_video] + overlay_clips)
    print(f"\nFinal video with overlays duration: {final_video.duration:.2f}s")

# Process audio
final_audio = None
for audio in config["audio"]:
    # Check if 'asset' key exists
    if "asset" not in audio:
        print(f"Warning: Missing 'asset' key in audio entry: {audio}")
        continue
        
    asset_name = audio["asset"]
    if asset_name in audio_assets:
        original_clip = audio_assets[asset_name]
        end_time = audio.get("end_time", original_clip.duration)
        audio_clip = safe_subclip(original_clip, audio["start_time"], end_time)
        
        if audio_clip is None:
            print(f"Warning: Invalid audio time range for '{asset_name}', skipping")
            continue
            
        # Use multiplication to adjust volume
        volume = audio.get("volume", 1.0)
        audio_clip = audio_clip * volume
        
        if final_audio is None:
            final_audio = audio_clip
        else:
            final_audio = final_audio.overlay(audio_clip)
        print(f"Added audio: '{asset_name}' from {audio['start_time']}s to {end_time}s with volume {volume}")
    else:
        print(f"Warning: Audio asset '{asset_name}' not found, skipping")

if final_audio:
    final_video = final_video.with_audio(final_audio)

# Write output
output_path = os.path.join(script_dir, "output_overlays.mp4")
print(f"\nRendering video to: {output_path}")
print(f"Final video duration: {final_video.duration:.2f}s")
final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

# Clean up
print("\nCleaning up resources...")
for clip in list(video_assets.values()) + list(gif_assets.values()) + list(image_assets.values()) + list(audio_assets.values()):
    if clip:
        clip.close()
print("Done!")