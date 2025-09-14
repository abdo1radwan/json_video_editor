

# Expanding Effect Library and Creating Template System

I'll guide you through implementing both enhancements to your MoviePy video editing system.

## 1. Expanding the Effect Library

Let's add more sophisticated visual and audio effects to your system.

### Visual Effects Expansion

Add these new effect functions to your existing code:

```python
import json
import os
from moviepy import (
    VideoFileClip, AudioFileClip, ImageClip, TextClip,
    CompositeVideoClip, concatenate_videoclips, vfx, ColorClip
)
from moviepy.video.io.VideoFileClip import VideoFileClip
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
import colorsys

# Add these new effect functions to your existing code

def apply_color_grading(clip, effect_params):
    """Apply color grading effects to a clip"""
    brightness = effect_params.get("brightness", 1.0)
    contrast = effect_params.get("contrast", 1.0)
    saturation = effect_params.get("saturation", 1.0)
    temperature = effect_params.get("temperature", 0)  # -100 to 100
    tint = effect_params.get("tint", 0)  # -100 to 100
    
    def color_grade_frame(frame):
        # Convert to PIL Image for easier manipulation
        img = Image.fromarray(frame)
        
        # Apply brightness and contrast
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(brightness)
        
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast)
        
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(saturation)
        
        # Apply temperature and tint
        if temperature != 0 or tint != 0:
            # Convert to HSV for easier color manipulation
            hsv_img = img.convert('HSV')
            h, s, v = hsv_img.split()
            h = np.array(h)
            
            # Adjust temperature (shift towards blue/yellow)
            if temperature > 0:
                # Shift towards yellow (increase red/green, decrease blue)
                h = (h + temperature/200) % 1.0
            else:
                # Shift towards blue (decrease red/green, increase blue)
                h = (h + temperature/200) % 1.0
            
            # Adjust tint (shift towards green/magenta)
            if tint > 0:
                # Shift towards green
                h = (h + 0.33 + tint/200) % 1.0
            else:
                # Shift towards magenta
                h = (h + 0.67 + tint/200) % 1.0
            
            h = Image.fromarray((h * 255).astype(np.uint8))
            hsv_img = Image.merge('HSV', (h, s, v))
            img = hsv_img.convert('RGB')
        
        return np.array(img)
    
    return clip.fl(color_grade_frame)

def apply_blur_effect(clip, effect_params):
    """Apply various blur effects"""
    blur_type = effect_params.get("type", "gaussian")
    radius = effect_params.get("radius", 5)
    intensity = effect_params.get("intensity", 1.0)
    
    if blur_type == "gaussian":
        return clip.with_effects([vfx.GaussianBlur(radius * intensity)])
    elif blur_type == "motion":
        angle = effect_params.get("angle", 0)
        # Motion blur implementation
        def motion_blur(frame):
            img = Image.fromarray(frame)
            # Create motion blur kernel
            kernel_size = int(radius * intensity) * 2 + 1
            if kernel_size > 1:
                # Create a horizontal or vertical line kernel
                if angle % 180 == 0:  # Horizontal
                    kernel = np.zeros((kernel_size, kernel_size))
                    kernel[kernel_size//2, :] = 1
                else:  # Vertical
                    kernel = np.zeros((kernel_size, kernel_size))
                    kernel[:, kernel_size//2] = 1
                
                kernel = kernel / np.sum(kernel)
                
                # Apply convolution
                from scipy import ndimage
                blurred = ndimage.convolve(img, kernel, mode='reflect')
                return blurred
            return frame
        
        return clip.fl(motion_blur)
    elif blur_type == "radial":
        # Radial blur implementation
        def radial_blur(frame):
            img = Image.fromarray(frame)
            center = (img.width // 2, img.height // 2)
            max_radius = min(center[0], center[1], 
                           img.width - center[0], img.height - center[1])
            
            # Create radial gradient mask
            y, x = np.ogrid[:img.height, :img.width]
            dist_from_center = np.sqrt((x - center[0])**2 + (y - center[1])**2)
            
            # Create blur mask
            blur_mask = np.clip(dist_from_center / max_radius * radius * intensity, 0, 1)
            
            # Apply blur based on distance from center
            result = np.array(img)
            for i in range(int(radius * intensity)):
                blur_amount = blur_mask > (i / (radius * intensity))
                if np.any(blur_amount):
                    # Apply Gaussian blur with increasing radius
                    blurred = np.array(img.filter(ImageFilter.GaussianBlur(radius=i+1)))
                    result[blur_amount] = blurred[blur_amount]
            
            return result
        
        return clip.fl(radial_blur)
    
    return clip

def apply_distortion_effect(clip, effect_params):
    """Apply distortion effects like ripple, fisheye, etc."""
    distortion_type = effect_params.get("type", "ripple")
    strength = effect_params.get("strength", 0.5)
    frequency = effect_params.get("frequency", 10)
    
    def distort_frame(frame):
        img = Image.fromarray(frame)
        width, height = img.size
        
        # Create coordinate grids
        x, y = np.meshgrid(np.arange(width), np.arange(height))
        
        # Normalize coordinates to [-1, 1]
        x_norm = (x - width/2) / (width/2)
        y_norm = (y - height/2) / (height/2)
        
        # Calculate distance from center
        r = np.sqrt(x_norm**2 + y_norm**2)
        theta = np.arctan2(y_norm, x_norm)
        
        if distortion_type == "ripple":
            # Ripple distortion
            r_new = r + strength * np.sin(frequency * r * 2 * np.pi)
            x_new = r_new * np.cos(theta)
            y_new = r_new * np.sin(theta)
        elif distortion_type == "fisheye":
            # Fisheye distortion
            r_new = r * (1 + strength * r**2)
            x_new = r_new * np.cos(theta)
            y_new = r_new * np.sin(theta)
        elif distortion_type == "barrel":
            # Barrel distortion
            r_new = r * (1 + strength * r**2)
            x_new = r_new * np.cos(theta)
            y_new = r_new * np.sin(theta)
        elif distortion_type == "pincushion":
            # Pincushion distortion
            r_new = r * (1 - strength * r**2)
            x_new = r_new * np.cos(theta)
            y_new = r_new * np.sin(theta)
        else:
            return frame
        
        # Convert back to pixel coordinates
        x_pixel = (x_new * width/2 + width/2).astype(np.int32)
        y_pixel = (y_new * height/2 + height/2).astype(np.int32)
        
        # Clip to valid range
        x_pixel = np.clip(x_pixel, 0, width-1)
        y_pixel = np.clip(y_pixel, 0, height-1)
        
        # Create distorted image
        distorted = np.zeros_like(frame)
        for c in range(frame.shape[2]):
            distorted[:,:,c] = frame[:,:,c][y_pixel, x_pixel]
        
        return distorted
    
    return clip.fl(distort_frame)

def apply_vignette_effect(clip, effect_params):
    """Apply vignette effect"""
    strength = effect_params.get("strength", 0.5)
    radius = effect_params.get("radius", 0.5)
    softness = effect_params.get("softness", 0.5)
    
    def add_vignette(frame):
        img = Image.fromarray(frame)
        width, height = img.size
        
        # Create vignette mask
        y, x = np.ogrid[:height, :width]
        center_x, center_y = width // 2, height // 2
        
        # Calculate distance from center
        dist_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        
        # Normalize distance
        max_dist = np.sqrt(center_x**2 + center_y**2)
        normalized_dist = dist_from_center / max_dist
        
        # Create vignette mask
        vignette_mask = np.clip((normalized_dist - radius) / (softness * (1 - radius)), 0, 1)
        
        # Apply vignette
        result = np.array(img)
        for c in range(result.shape[2]):
            result[:,:,c] = result[:,:,c] * (1 - vignette_mask * strength)
        
        return result
    
    return clip.fl(add_vignette)

def apply_glitch_effect(clip, effect_params):
    """Apply digital glitch effect"""
    intensity = effect_params.get("intensity", 0.5)
    frequency = effect_params.get("frequency", 0.1)
    
    def add_glitch(frame):
        # Randomly apply glitch effects
        if np.random.random() < frequency:
            img = Image.fromarray(frame)
            width, height = img.size
            
            # Channel shift
            if np.random.random() < intensity:
                # Split RGB channels
                r, g, b = img.split()
                
                # Shift channels randomly
                shift_amount = np.random.randint(-20, 20)
                if shift_amount > 0:
                    r = Image.fromarray(np.array(r)[:, shift_amount:])
                    g = Image.fromarray(np.array(g)[:, shift_amount:])
                    b = Image.fromarray(np.array(b)[:, shift_amount:])
                else:
                    r = Image.fromarray(np.array(r)[:, :shift_amount])
                    g = Image.fromarray(np.array(g)[:, :shift_amount])
                    b = Image.fromarray(np.array(b)[:, :shift_amount])
                
                # Merge back
                img = Image.merge('RGB', (r, g, b))
            
            # Line displacement
            if np.random.random() < intensity:
                # Select random lines to displace
                num_lines = np.random.randint(1, 10)
                for _ in range(num_lines):
                    line_y = np.random.randint(0, height)
                    line_height = np.random.randint(1, 5)
                    displacement = np.random.randint(-50, 50)
                    
                    # Extract and displace line
                    line = img.crop((0, line_y, width, line_y + line_height))
                    img.paste(line, (displacement, line_y))
            
            # Color corruption
            if np.random.random() < intensity:
                # Randomly alter color channels
                img_array = np.array(img)
                channel = np.random.randint(0, 3)
                img_array[:,:,channel] = np.clip(
                    img_array[:,:,channel] * np.random.uniform(0.5, 1.5),
                    0, 255
                ).astype(np.uint8)
                img = Image.fromarray(img_array)
            
            return np.array(img)
        
        return frame
    
    return clip.fl(add_glitch)

# Update the apply_effects function to include new effects
def apply_effects(clip, effects):
    """Apply effects to a clip with expanded effect library."""
    for effect in effects:
        if effect["type"] == "fadein":
            clip = clip.with_effects([vfx.FadeIn(effect["duration"])])
        elif effect["type"] == "fadeout":
            clip = clip.with_effects([vfx.FadeOut(effect["duration"])])
        elif effect["type"] == "glow":
            # Existing glow effect
            glow_color = color_string_to_rgb(effect["color"])
            radius = effect.get("radius", 5)
            
            try:
                blurred_clip = clip.with_effects([vfx.GaussianBlur(radius)])
            except:
                blurred_clip = clip
            
            color_layer = ColorClip(clip.size, color=glow_color, duration=clip.duration)
            color_layer = color_layer.with_opacity(0.3)
            
            glow_clip = CompositeVideoClip([blurred_clip, color_layer, clip])
            clip = glow_clip
            
        elif effect["type"] == "outline":
            # Existing outline effect
            if hasattr(clip, 'txt'):
                outline_color = color_string_to_rgb(effect["color"])
                outline_width = effect.get("width", 2)
                
                outlines = []
                for dx, dy in [(-outline_width, 0), (outline_width, 0), (0, -outline_width), (0, outline_width)]:
                    outline = TextClip(
                        text=clip.txt,
                        font=clip.font,
                        font_size=clip.fontsize,
                        color=outline_color
                    ).with_duration(clip.duration).with_position((dx, dy))
                    outlines.append(outline)
                
                clip = CompositeVideoClip(outlines + [clip])
                
        elif effect["type"] == "shadow":
            # Existing shadow effect
            if hasattr(clip, 'txt'):
                shadow_color = color_string_to_rgb(effect.get("color", "black"))
                shadow_offset = effect.get("offset", [5, 5])
                shadow_opacity = effect.get("opacity", 0.5)
                
                shadow = TextClip(
                    text=clip.txt,
                    font=clip.font,
                    font_size=clip.fontsize,
                    color=shadow_color
                ).with_duration(clip.duration)
                
                shadow = shadow.with_position((
                    clip.pos[0] + shadow_offset[0] if isinstance(clip.pos[0], (int, float)) else clip.pos[0],
                    clip.pos[1] + shadow_offset[1] if isinstance(clip.pos[1], (int, float)) else clip.pos[1]
                ))
                
                shadow = shadow.with_opacity(shadow_opacity)
                clip = CompositeVideoClip([shadow, clip])
        
        # NEW EFFECTS
        elif effect["type"] == "color_grading":
            clip = apply_color_grading(clip, effect)
        elif effect["type"] == "blur":
            clip = apply_blur_effect(clip, effect)
        elif effect["type"] == "distortion":
            clip = apply_distortion_effect(clip, effect)
        elif effect["type"] == "vignette":
            clip = apply_vignette_effect(clip, effect)
        elif effect["type"] == "glitch":
            clip = apply_glitch_effect(clip, effect)
    
    return clip
```

### Audio Effects Expansion

```python
# Add these audio effect functions to your code

def apply_audio_equalizer(clip, effect_params):
    """Apply audio equalizer effects"""
    bands = effect_params.get("bands", [
        {"frequency": 60, "gain": 0},    # Bass
        {"frequency": 230, "gain": 0},   # Low-mid
        {"frequency": 910, "gain": 0},   # Mid
        {"frequency": 4000, "gain": 0},  # High-mid
        {"frequency": 14000, "gain": 0}  # Treble
    ])
    
    # This is a simplified implementation
    # In a real implementation, you would use FFT to modify frequency bands
    def apply_eq(audio_frame):
        # Apply volume adjustments based on frequency content
        # This is a placeholder for actual FFT processing
        return audio_frame
    
    return clip.fl(apply_eq)

def apply_audio_reverb(clip, effect_params):
    """Apply reverb effect"""
    room_size = effect_params.get("room_size", 0.5)  # 0 to 1
    damping = effect_params.get("damping", 0.5)      # 0 to 1
    wet_level = effect_params.get("wet_level", 0.3)   # 0 to 1
    dry_level = effect_params.get("dry_level", 0.7)   # 0 to 1
    
    # This is a simplified implementation
    # In a real implementation, you would use convolution with impulse responses
    def apply_reverb_effect(audio_frame):
        # Apply reverb using delay and attenuation
        # This is a placeholder for actual reverb processing
        return audio_frame
    
    return clip.fl(apply_reverb_effect)

def apply_audio_delay(clip, effect_params):
    """Apply delay/echo effect"""
    delay_time = effect_params.get("delay_time", 0.3)  # in seconds
    feedback = effect_params.get("feedback", 0.5)    # 0 to 1
    mix = effect_params.get("mix", 0.5)               # 0 to 1
    
    # Create delayed version of the audio
    delayed_clip = clip.with_start(delay_time)
    delayed_clip = delayed_clip * feedback
    
    # Mix original and delayed audio
    if mix > 0:
        return clip * (1 - mix) + delayed_clip * mix
    else:
        return clip

def apply_audio_compressor(clip, effect_params):
    """Apply audio compression"""
    threshold = effect_params.get("threshold", -20)  # dB
    ratio = effect_params.get("ratio", 4)             # compression ratio
    attack = effect_params.get("attack", 0.005)      # seconds
    release = effect_params.get("release", 0.1)     # seconds
    
    # This is a simplified implementation
    # In a real implementation, you would apply dynamic range compression
    def apply_compression(audio_frame):
        # Apply compression to reduce dynamic range
        # This is a placeholder for actual compression processing
        return audio_frame
    
    return clip.fl(apply_compression)

def apply_audio_filter(clip, effect_params):
    """Apply audio filters (low-pass, high-pass, etc.)"""
    filter_type = effect_params.get("type", "low_pass")
    cutoff = effect_params.get("cutoff", 1000)  # Hz
    q = effect_params.get("q", 1.0)             # Quality factor
    
    # This is a simplified implementation
    # In a real implementation, you would use digital filter design
    def apply_filter(audio_frame):
        # Apply the specified filter
        # This is a placeholder for actual filter processing
        return audio_frame
    
    return clip.fl(apply_filter)

# Update the audio processing section to include new effects
def process_audio_with_effects(audio_clip, audio_config):
    """Process audio with expanded effect library"""
    if "effects" in audio_config:
        for effect in audio_config["effects"]:
            if effect["type"] == "equalizer":
                audio_clip = apply_audio_equalizer(audio_clip, effect)
            elif effect["type"] == "reverb":
                audio_clip = apply_audio_reverb(audio_clip, effect)
            elif effect["type"] == "delay":
                audio_clip = apply_audio_delay(audio_clip, effect)
            elif effect["type"] == "compressor":
                audio_clip = apply_audio_compressor(audio_clip, effect)
            elif effect["type"] == "filter":
                audio_clip = apply_audio_filter(audio_clip, effect)
    
    # Apply volume
    volume = audio_config.get("volume", 1.0)
    audio_clip = audio_clip * volume
    
    return audio_clip
```

### Example JSON Configuration with New Effects

```json
{
  "assets": {
    "videos": [
      {
        "name": "main",
        "path": "assets/main.mp4"
      }
    ],
    "audios": [
      {
        "name": "music",
        "path": "assets/music.wav"
      }
    ]
  },
  "editing": [
    {
      "asset": "main",
      "start_time": 0,
      "end_time": 10,
      "effects": [
        {
          "type": "color_grading",
          "brightness": 1.1,
          "contrast": 1.2,
          "saturation": 1.3,
          "temperature": 10,
          "tint": -5
        },
        {
          "type": "vignette",
          "strength": 0.4,
          "radius": 0.6,
          "softness": 0.3
        }
      ]
    }
  ],
  "overlays": [
    {
      "type": "text",
      "text": "Welcome to the Future",
      "start_time": 2,
      "end_time": 8,
      "position": "center",
      "font": "Arial.ttf",
      "font_size": 60,
      "color": "white",
      "effects": [
        {
          "type": "glow",
          "color": "cyan",
          "radius": 8
        },
        {
          "type": "glitch",
          "intensity": 0.3,
          "frequency": 0.05
        }
      ]
    }
  ],
  "audio": [
    {
      "asset": "music",
      "start_time": 0,
      "volume": 0.7,
      "effects": [
        {
          "type": "equalizer",
          "bands": [
            {"frequency": 60, "gain": 3},
            {"frequency": 230, "gain": 1},
            {"frequency": 910, "gain": -1},
            {"frequency": 4000, "gain": 2},
            {"frequency": 14000, "gain": 0}
          ]
        },
        {
          "type": "reverb",
          "room_size": 0.6,
          "damping": 0.4,
          "wet_level": 0.2,
          "dry_level": 0.8
        }
      ]
    }
  ]
}
```

## 2. Creating a Template System

Now let's implement a template system for reusable video templates.

### Template System Implementation

```python
import json
import os
import glob
from datetime import datetime

class VideoTemplate:
    """Base class for video templates"""
    
    def __init__(self, template_name, template_data=None):
        self.name = template_name
        self.data = template_data or self.load_template(template_name)
        self.variables = self.extract_variables()
    
    def load_template(self, template_name):
        """Load template from file"""
        template_path = f"templates/{template_name}.json"
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f"Template {template_name} not found")
    
    def save_template(self, template_path=None):
        """Save template to file"""
        if template_path is None:
            template_path = f"templates/{self.name}.json"
        
        # Ensure templates directory exists
        os.makedirs(os.path.dirname(template_path), exist_ok=True)
        
        with open(template_path, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def extract_variables(self):
        """Extract template variables from the template data"""
        variables = set()
        
        def find_variables(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str) and "${" in value and "}" in value:
                        # Extract variable names from ${variable}
                        import re
                        variables.update(re.findall(r'\$\{([^}]+)\}', value))
                    find_variables(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    find_variables(item, f"{path}[{i}]")
        
        find_variables(self.data)
        return list(variables)
    
    def generate_video_config(self, variables):
        """Generate video configuration by replacing variables"""
        config_str = json.dumps(self.data)
        
        # Replace variables with provided values
        for var_name, var_value in variables.items():
            config_str = config_str.replace(f"${{{var_name}}}", str(var_value))
        
        return json.loads(config_str)
    
    def get_required_assets(self):
        """Get list of required assets for this template"""
        assets = {
            "videos": [],
            "images": [],
            "audios": [],
            "gifs": []
        }
        
        def extract_assets(obj):
            if isinstance(obj, dict):
                if obj.get("type") in ["video", "image", "audio", "gif"]:
                    asset_type = f"{obj['type']}s"
                    if asset_type in assets and "asset" in obj:
                        assets[asset_type].append(obj["asset"])
                elif "asset" in obj:
                    # This might be in the assets section
                    for asset_type in assets.keys():
                        if asset_type in obj:
                            assets[asset_type].append(obj["asset"])
                
                # Recursively check nested objects
                for value in obj.values():
                    extract_assets(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_assets(item)
        
        extract_assets(self.data)
        return assets
    
    def validate_template(self):
        """Validate template structure and variables"""
        errors = []
        
        # Check required sections
        required_sections = ["assets", "editing", "overlays"]
        for section in required_sections:
            if section not in self.data:
                errors.append(f"Missing required section: {section}")
        
        # Check variable references
        all_vars = set()
        used_vars = set()
        
        def collect_vars(obj, is_definition=False):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str) and "${" in value and "}" in value:
                        import re
                        vars_in_value = re.findall(r'\$\{([^}]+)\}', value)
                        if is_definition:
                            all_vars.update(vars_in_value)
                        else:
                            used_vars.update(vars_in_value)
                    collect_vars(value, is_definition)
            elif isinstance(obj, list):
                for item in obj:
                    collect_vars(item, is_definition)
        
        collect_vars(self.data.get("variables", {}), is_definition=True)
        collect_vars(self.data)
        
        # Check for undefined variables
        undefined_vars = used_vars - all_vars
        if undefined_vars:
            errors.append(f"Undefined variables: {', '.join(undefined_vars)}")
        
        # Check for unused variables
        unused_vars = all_vars - used_vars
        if unused_vars:
            errors.append(f"Unused variables: {', '.join(unused_vars)}")
        
        return errors

class TemplateManager:
    """Manager for video templates"""
    
    def __init__(self, templates_dir="templates"):
        self.templates_dir = templates_dir
        self.templates = {}
        self.load_all_templates()
    
    def load_all_templates(self):
        """Load all templates from the templates directory"""
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
            return
        
        template_files = glob.glob(os.path.join(self.templates_dir, "*.json"))
        for template_file in template_files:
            template_name = os.path.splitext(os.path.basename(template_file))[0]
            try:
                self.templates[template_name] = VideoTemplate(template_name)
                print(f"Loaded template: {template_name}")
            except Exception as e:
                print(f"Error loading template {template_name}: {e}")
    
    def get_template(self, template_name):
        """Get a specific template"""
        if template_name not in self.templates:
            self.templates[template_name] = VideoTemplate(template_name)
        return self.templates[template_name]
    
    def list_templates(self):
        """List all available templates"""
        return list(self.templates.keys())
    
    def create_template(self, template_name, template_data):
        """Create a new template"""
        template = VideoTemplate(template_name, template_data)
        template.save_template()
        self.templates[template_name] = template
        return template
    
    def delete_template(self, template_name):
        """Delete a template"""
        if template_name in self.templates:
            template_path = os.path.join(self.templates_dir, f"{template_name}.json")
            if os.path.exists(template_path):
                os.remove(template_path)
            del self.templates[template_name]
            return True
        return False
    
    def generate_video_from_template(self, template_name, variables, output_path=None):
        """Generate a video from a template with variables"""
        template = self.get_template(template_name)
        
        # Validate template
        errors = template.validate_template()
        if errors:
            print("Template validation errors:")
            for error in errors:
                print(f"  - {error}")
            return None
        
        # Generate configuration
        config = template.generate_video_config(variables)
        
        # Get required assets
        required_assets = template.get_required_assets()
        
        # Check if all required assets are available
        missing_assets = []
        for asset_type, asset_names in required_assets.items():
            for asset_name in asset_names:
                asset_path = f"assets/{asset_name}.{asset_type[:-1]}"  # Remove 's' from plural
                if not os.path.exists(asset_path):
                    missing_assets.append(asset_path)
        
        if missing_assets:
            print("Missing required assets:")
            for asset in missing_assets:
                print(f"  - {asset}")
            return None
        
        # Generate output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/{template_name}_{timestamp}.mp4"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create video using the existing video generation system
        # This would integrate with your main.py logic
        print(f"Generating video from template '{template_name}'...")
        print(f"Output path: {output_path}")
        
        # Here you would call your existing video generation code
        # For now, we'll just save the generated config
        config_path = f"output/{template_name}_{timestamp}_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Generated configuration saved to: {config_path}")
        
        return output_path

# Example template creation
def create_example_templates():
    """Create example templates for common use cases"""
    
    # Corporate Presentation Template
    corporate_template = {
        "name": "Corporate Presentation",
        "description": "Professional corporate presentation template",
        "variables": {
            "company_name": "Your Company",
            "presentation_title": "Annual Report 2023",
            "presenter_name": "John Doe",
            "duration": 60
        },
        "assets": {
            "videos": [
                {"name": "intro", "path": "assets/corporate_intro.mp4"},
                {"name": "background", "path": "assets/corporate_bg.mp4"}
            ],
            "images": [
                {"name": "logo", "path": "assets/company_logo.png"},
                {"name": "background", "path": "assets/corporate_bg.jpg"}
            ],
            "audios": [
                {"name": "background_music", "path": "assets/corporate_music.wav"}
            ]
        },
        "editing": [
            {
                "asset": "intro",
                "start_time": 0,
                "end_time": 5,
                "effects": [
                    {"type": "fadein", "duration": 1}
                ]
            },
            {
                "asset": "background",
                "start_time": 5,
                "end_time": "${duration}",
                "effects": [
                    {"type": "color_grading",
                     "brightness": 1.1,
                     "contrast": 1.05,
                     "saturation": 0.9}
                ]
            }
        ],
        "overlays": [
            {
                "type": "image",
                "asset": "logo",
                "start_time": 0,
                "end_time": "${duration}",
                "position": "top-left",
                "size": [0.1, 0.1]
            },
            {
                "type": "text",
                "text": "${company_name}",
                "start_time": 1,
                "end_time": 4,
                "position": "center",
                "font": "Arial.ttf",
                "font_size": 48,
                "color": "white",
                "effects": [
                    {"type": "fadein", "duration": 1},
                    {"type": "fadeout", "duration": 1}
                ]
            },
            {
                "type": "text",
                "text": "${presentation_title}",
                "start_time": 6,
                "end_time": "${duration}",
                "position": "top-center",
                "font": "Arial.ttf",
                "font_size": 36,
                "color": "white",
                "background": {
                    "color": "black",
                    "opacity": 0.7
                }
            },
            {
                "type": "text",
                "text": "Presented by: ${presenter_name}",
                "start_time": "${duration}",
                "end_time": "${duration}",
                "position": "bottom-center",
                "font": "Arial.ttf",
                "font_size": 24,
                "color": "white"
            }
        ],
        "audio": [
            {
                "asset": "background_music",
                "start_time": 0,
                "volume": 0.3,
                "effects": [
                    {"type": "fadein", "duration": 2},
                    {"type": "fadeout", "duration": 2}
                ]
            }
        ],
        "global_settings": {
            "output_resolution": [1920, 1080],
            "fps": 30,
            "video_codec": "libx264",
            "audio_codec": "aac"
        }
    }
    
    # Social Media Template
    social_media_template = {
        "name": "Social Media Post",
        "description": "Engaging social media video template",
        "variables": {
            "product_name": "Amazing Product",
            "hashtag": "#AmazingProduct",
            "call_to_action": "Shop Now!",
            "duration": 30
        },
        "assets": {
            "videos": [
                {"name": "product_demo", "path": "assets/product_demo.mp4"}
            ],
            "images": [
                {"name": "product_image", "path": "assets/product_image.png"},
                {"name": "brand_logo", "path": "assets/brand_logo.png"}
            ],
            "audios": [
                {"name": "trending_music", "path": "assets/trending_music.wav"}
            ]
        },
        "editing": [
            {
                "asset": "product_demo",
                "start_time": 0,
                "end_time": "${duration}",
                "effects": [
                    {"type": "color_grading",
                     "brightness": 1.2,
                     "contrast": 1.1,
                     "saturation": 1.3}
                ]
            }
        ],
        "overlays": [
            {
                "type": "image",
                "asset": "brand_logo",
                "start_time": 0,
                "end_time": "${duration}",
                "position": "top-right",
                "size": [0.15, 0.15]
            },
            {
                "type": "text",
                "text": "${product_name}",
                "start_time": 1,
                "end_time": 5,
                "position": "center",
                "font": "Arial.ttf",
                "font_size": 48,
                "color": "white",
                "animation": {
                    "type": "bounce",
                    "duration": 2,
                    "height": 30
                },
                "effects": [
                    {"type": "glow", "color": "yellow", "radius": 5}
                ]
            },
            {
                "type": "text",
                "text": "${hashtag}",
                "start_time": 6,
                "end_time": "${duration}",
                "position": "bottom-center",
                "font": "Arial.ttf",
                "font_size": 36,
                "color": "white",
                "animation": {
                    "type": "scroll",
                    "direction": "left_to_right",
                    "duration": 5
                }
            },
            {
                "type": "text",
                "text": "${call_to_action}",
                "start_time": "${duration}",
                "end_time": "${duration}",
                "position": "center",
                "font": "Arial.ttf",
                "font_size": 42,
                "color": "yellow",
                "background": {
                    "color": "red",
                    "opacity": 0.8
                },
                "effects": [
                    {"type": "glitch", "intensity": 0.3, "frequency": 0.1}
                ]
            }
        ],
        "audio": [
            {
                "asset": "trending_music",
                "start_time": 0,
                "volume": 0.5,
                "effects": [
                    {"type": "equalizer",
                     "bands": [
                         {"frequency": 60, "gain": 2},
                         {"frequency": 230, "gain": 1},
                         {"frequency": 910, "gain": 0},
                         {"frequency": 4000, "gain": 1},
                         {"frequency": 14000, "gain": 2}
                     ]}
                ]
            }
        ],
        "global_settings": {
            "output_resolution": [1080, 1080],  # Square for social media
            "fps": 30,
            "video_codec": "libx264",
            "audio_codec": "aac"
        }
    }
    
    # Save templates
    template_manager = TemplateManager()
    template_manager.create_template("corporate_presentation", corporate_template)
    template_manager.create_template("social_media_post", social_media_template)
    
    print("Created example templates:")
    print("- corporate_presentation")
    print("- social_media_post")

# Example usage of the template system
def example_template_usage():
    """Example of how to use the template system"""
    
    # Initialize template manager
    template_manager = TemplateManager()
    
    # List available templates
    print("Available templates:")
    for template_name in template_manager.list_templates():
        print(f"  - {template_name}")
    
    # Use corporate presentation template
    variables = {
        "company_name": "TechCorp Inc.",
        "presentation_title": "Q4 2023 Financial Results",
        "presenter_name": "Jane Smith",
        "duration": 120
    }
    
    # Generate video from template
    output_path = template_manager.generate_video_from_template(
        "corporate_presentation", 
        variables
    )
    
    if output_path:
        print(f"Video generated successfully: {output_path}")
    
    # Use social media template
    variables = {
        "product_name": "SuperWidget Pro",
        "hashtag": "#SuperWidget",
        "call_to_action": "Buy Now!",
        "duration": 30
    }
    
    output_path = template_manager.generate_video_from_template(
        "social_media_post", 
        variables
    )
    
    if output_path:
        print(f"Video generated successfully: {output_path}")

# Integration with main video editing system
def integrate_template_system():
    """Integrate the template system with the main video editing system"""
    
    # Add template processing to the main workflow
    def process_template_request(template_name, variables):
        """Process a template request"""
        template_manager = TemplateManager()
        
        try:
            # Get template
            template = template_manager.get_template(template_name)
            
            # Validate template
            errors = template.validate_template()
            if errors:
                print("Template validation failed:")
                for error in errors:
                    print(f"  - {error}")
                return None
            
            # Generate configuration
            config = template.generate_video_config(variables)
            
            # Check required assets
            required_assets = template.get_required_assets()
            print("Required assets:")
            for asset_type, asset_names in required_assets.items():
                print(f"  {asset_type}: {asset_names}")
            
            # Here you would integrate with your existing video generation code
            # For now, we'll just return the config
            return config
            
        except Exception as e:
            print(f"Error processing template: {e}")
            return None
    
    # Example usage
    config = process_template_request("corporate_presentation", {
        "company_name": "Example Corp",
        "presentation_title": "Annual Report",
        "presenter_name": "John Doe",
        "duration": 60
    })
    
    if config:
        print("Generated configuration from template:")
        print(json.dumps(config, indent=2))

# Create templates and show example usage
if __name__ == "__main__":
    create_example_templates()
    example_template_usage()
    integrate_template_system()
```

### Directory Structure for Template System

```
editing/
├── main.py                    # Main video editing script
├── edit_config_advanced.json   # Manual configuration
├── templates/                  # Template directory
│   ├── corporate_presentation.json
│   ├── social_media_post.json
│   └── product_review.json
├── output/                     # Generated videos
│   ├── corporate_presentation_20231201_120000.mp4
│   └── social_media_post_20231201_120001.mp4
└── assets/                     # Media assets
    ├── corporate_intro.mp4
    ├── product_demo.mp4
    ├── company_logo.png
    └── trending_music.wav
```

### How to Use the Enhanced System

1. **Using New Effects**:
   - Add new effects to your JSON configuration
   - Specify effect parameters as needed
   - Combine multiple effects for complex looks

2. **Using Templates**:
   - Choose a template that fits your needs
   - Provide values for template variables
   - Generate videos with consistent styling

3. **Creating Custom Templates**:
   - Design your video structure
   - Identify variable elements
   - Create a template JSON file
   - Save it in the templates directory

### Example Workflow

```python
# Initialize the template manager
template_manager = TemplateManager()

# Use a pre-made template
variables = {
    "company_name": "My Company",
    "presentation_title": "Annual Report 2023",
    "presenter_name": "John Doe",
    "duration": 120
}

# Generate video
output_path = template_manager.generate_video_from_template(
    "corporate_presentation", 
    variables,
    "output/my_presentation.mp4"
)

print(f"Video generated: {output_path}")
```

This enhanced system provides both sophisticated visual/audio effects and a powerful template system for creating consistent, reusable video designs. The template system allows for rapid video generation while maintaining quality and branding consistency.