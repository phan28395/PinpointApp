# PinPoint Plugin Development Guide

## Quick Start (5 minutes)

### 1. Install Plugin Development Kit
```bash
pip install pinpoint-pdk
```

### 2. Create Your Plugin
```bash
pinpoint-pdk create my-awesome-plugin
cd my-awesome-plugin
```

### 3. Edit Your Plugin
```python
# my_awesome_plugin.py
from pinpoint.plugin_architecture import PluginBase

class MyAwesomePlugin(PluginBase):
    def setup_content(self):
        # Your plugin's UI goes here
        label = self.factory.create_label("Hello World!")
        button = self.factory.create_button("Click Me!")
        
        # Add to your content area
        self.content_layout.addWidget(label)
        self.content_layout.addWidget(button)
        
        # Connect functionality
        button.clicked.connect(self.on_button_click)
    
    def on_button_click(self):
        print("Button clicked!")
```

### 4. Test Your Plugin
```bash
pinpoint-pdk test
```

### 5. Submit to Marketplace
```bash
pinpoint-pdk submit
```

## What You Get For Free

### ✅ **Automatic UI Consistency**
Your plugin automatically gets:
- Proper window chrome (header, close button)
- Drag and resize functionality
- Theme support (dark/light modes)
- Consistent spacing and typography

### ✅ **Built-in Security**
- Sandboxed execution
- Permission system
- Secure API for network/file access
- Data isolation

### ✅ **Easy Data Storage**
```python
# Save data
self.save_data("user_preferences", {"theme": "dark"})

# Load data
prefs = self.load_data("user_preferences")
```

### ✅ **Simple Styling**
```json
// design.json - Style your content area
{
  "content_styles": {
    "background": "linear-gradient(to right, #667eea, #764ba2)",
    "padding": "20px",
    "border_radius": "8px"
  }
}
```

## Plugin Anatomy

```
my-awesome-plugin/
├── manifest.json        # Plugin metadata
├── __init__.py         # Plugin entry point
├── design.json         # Custom styles (optional)
├── assets/            # Images, icons (optional)
│   └── icon.png
└── README.md          # Documentation
```

### manifest.json
```json
{
  "id": "com.yourname.awesome",
  "name": "Awesome Plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "Does awesome things",
  "min_app_version": "1.0.0",
  "required_permissions": [],
  "optional_permissions": ["network_access"],
  "design_compliance_level": "strict"
}
```

## Available APIs

### 1. **UI Creation**
```python
# Create any standard widget
label = self.factory.create_label("Text")
button = self.factory.create_button("Click")
text_edit = self.factory.create_text_edit()
combo = self.factory.create_combo_box()
```

### 2. **Data Storage**
```python
# Save/load data (automatically sandboxed)
self.save_data("key", value)
value = self.load_data("key", default=None)
```

### 3. **Network Requests** (with permission)
```python
try:
    data = self.api.make_request("https://api.example.com/data")
except PermissionError:
    self.show_message("This plugin needs network access")
```

### 4. **User Interaction**
```python
# Show notifications
self.show_notification("Task completed!")

# Get user input
name = self.get_user_input("Enter your name:")

# Show progress
self.show_progress(0.5, "Processing...")
```

## Design Guidelines

### Do's ✅
- Use the provided factory methods for widgets
- Follow the color scheme for consistency
- Request only necessary permissions
- Handle errors gracefully
- Provide clear documentation

### Don'ts ❌
- Don't try to style core UI elements
- Don't access files directly (use API)
- Don't make network requests without permission
- Don't store sensitive data unencrypted
- Don't use exec() or eval()

## Examples

### Weather Widget
```python
class WeatherPlugin(PluginBase):
    def setup_content(self):
        self.temp_label = self.factory.create_label("--°")
        self.temp_label.setObjectName("temperature")
        self.content_layout.addWidget(self.temp_label)
        
        # Request weather data
        self.refresh_weather()
    
    async def refresh_weather(self):
        try:
            data = await self.api.fetch_json(
                "https://api.weather.com/current"
            )
            self.temp_label.setText(f"{data['temp']}°")
        except PermissionError:
            self.temp_label.setText("Need network permission")
```

### Todo List
```python
class TodoPlugin(PluginBase):
    def setup_content(self):
        # Create UI
        self.input = self.factory.create_line_edit()
        self.add_btn = self.factory.create_button("Add")
        self.list = self.factory.create_list_widget()
        
        # Layout
        self.content_layout.addWidget(self.input)
        self.content_layout.addWidget(self.add_btn)
        self.content_layout.addWidget(self.list)
        
        # Connect
        self.add_btn.clicked.connect(self.add_todo)
        
        # Load saved todos
        self.load_todos()
    
    def add_todo(self):
        text = self.input.text()
        if text:
            self.list.addItem(text)
            self.input.clear()
            self.save_todos()
```

## Testing Your Plugin

### 1. **Unit Tests**
```python
def test_plugin_creation():
    plugin = MyAwesomePlugin(test_data, test_design)
    assert plugin.label.text() == "Hello World!"
```

### 2. **Integration Tests**
```bash
# Test with the PDK
pinpoint-pdk test --integration
```

### 3. **Design Compliance**
```bash
# Check if your design follows guidelines
pinpoint-pdk validate-design
```

## Publishing

### 1. **Validate**
```bash
pinpoint-pdk validate
✓ Manifest valid
✓ No security issues
✓ Design compliant
✓ Tests passing
```

### 2. **Package**
```bash
pinpoint-pdk package
Created: my-awesome-plugin-1.0.0.ppk
```

### 3. **Submit**
```bash
pinpoint-pdk submit my-awesome-plugin-1.0.0.ppk
```

## Monetization

You can monetize your plugins through:
- **One-time purchase** - Users pay once
- **Subscription** - Monthly/yearly payments
- **Freemium** - Basic free, premium features paid
- **Donations** - Optional user support

## Getting Help

- 📚 Full API Documentation: https://pinpoint.dev/api
- 💬 Developer Forum: https://forum.pinpoint.dev
- 🐛 Report Issues: https://github.com/pinpoint/plugins
- 📧 Email Support: plugins@pinpoint.dev

## Best Practices

1. **Start Simple** - Get a basic version working first
2. **Handle Errors** - Always expect things to fail
3. **Respect Privacy** - Only request needed permissions
4. **Test Thoroughly** - Test on different themes/sizes
5. **Document Well** - Help users understand your plugin